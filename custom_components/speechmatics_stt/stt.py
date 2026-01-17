"""Speechmatics STT entity implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechToTextEntity,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from speechmatics.rt import (
    AsyncClient,
    AudioEncoding,
    AudioFormat,
    ConnectionSettings,
    OperatingPoint,
    ServerMessageType,
    TranscriptResult,
    TranscriptionConfig,
)

from .const import (
    DOMAIN,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    DEFAULT_OPERATING_POINT,
    DEFAULT_MAX_DELAY,
    DEFAULT_CHUNK_SIZE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Speechmatics STT entity from config entry."""
    config = config_entry.data

    entity = SpeechmaticsSTTEntity(
        api_key=config["api_key"],
        language=config.get("language", DEFAULT_LANGUAGE),
        operating_point=config.get("operating_point", DEFAULT_OPERATING_POINT),
        max_delay=config.get("max_delay", DEFAULT_MAX_DELAY),
    )

    async_add_entities([entity])


class SpeechmaticsSTTEntity(SpeechToTextEntity):
    """Speechmatics STT entity."""

    def __init__(
        self,
        api_key: str,
        language: str = DEFAULT_LANGUAGE,
        operating_point: str = DEFAULT_OPERATING_POINT,
        max_delay: float = DEFAULT_MAX_DELAY,
    ) -> None:
        """Initialize Speechmatics STT entity."""
        self._api_key = api_key
        self._language = language
        self._operating_point = operating_point
        self._max_delay = max_delay
        self._attr_name = "Speechmatics STT"
        self._attr_unique_id = f"{DOMAIN}_{language}"
        self._attr_available = True

        if not api_key or len(api_key) < 10:
            _LOGGER.warning("Invalid API key provided")
            self._attr_available = False

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return SUPPORTED_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return list of supported audio formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return list of supported audio codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return list of supported sample rates."""
        return [
            AudioSampleRates.SAMPLERATE_16000,
            AudioSampleRates.SAMPLERATE_44100,
        ]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return list of supported audio channels."""
        return [AudioChannels.CHANNEL_MONO]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return list of supported bit rates."""
        return [AudioBitRates.BITRATE_16]

    async def async_process_audio_stream(
        self,
        metadata: SpeechMetadata,
        stream: Any,
    ) -> SpeechResult:
        """Process audio stream and return transcription."""
        if not self._attr_available:
            return SpeechResult(
                text="",
                result=SpeechResultState.ERROR,
                error="Entity is unavailable - check API key configuration",
            )

        _LOGGER.debug(
            "Processing audio stream: language=%s, format=%s, codec=%s, "
            "sample_rate=%s, channel=%s",
            metadata.language,
            metadata.format,
            metadata.codec,
            metadata.sample_rate,
            metadata.channel,
        )

        transcript_parts = []
        error_message = None
        result_state = SpeechResultState.SUCCESS

        try:
            operating_point_enum = (
                OperatingPoint.ENHANCED
                if self._operating_point == "enhanced"
                else OperatingPoint.STANDARD
            )

            transcription_config = TranscriptionConfig(
                language=metadata.language or self._language,
                max_delay=self._max_delay,
                enable_partials=False,
                operating_point=operating_point_enum,
            )

            audio_format = AudioFormat(
                encoding=AudioEncoding.PCM_S16LE,
                chunk_size=DEFAULT_CHUNK_SIZE,
                sample_rate=metadata.sample_rate or 16000,
            )

            # Создаем ConnectionSettings для AsyncClient
            # Блокирующие SSL операции будут выполнены внутри AsyncClient
            connection_settings = ConnectionSettings(
                url="wss://eu2.rt.speechmatics.com/v2",
                auth_token=self._api_key,
            )
            
            async with AsyncClient(connection_settings) as client:
                transcript_future = asyncio.Future()

                @client.on(ServerMessageType.ADD_TRANSCRIPT)
                def handle_final_transcript(message: dict) -> None:
                    """Handle final transcript message."""
                    try:
                        result = TranscriptResult.from_message(message)
                        transcript = result.metadata.transcript
                        if transcript:
                            _LOGGER.debug("Received final transcript: %s", transcript)
                            transcript_parts.append(transcript)
                            if not transcript_future.done():
                                transcript_future.set_result(transcript)
                    except Exception as e:
                        _LOGGER.error("Error processing transcript: %s", e)
                        if not transcript_future.done():
                            transcript_future.set_exception(e)

                @client.on(ServerMessageType.ERROR)
                def handle_error(message: dict) -> None:
                    """Handle error message."""
                    error_msg = message.get("message", "Unknown error")
                    error_code = message.get("code", "")
                    _LOGGER.error(
                        "Speechmatics error: %s (code: %s)", error_msg, error_code
                    )

                    if error_code == "authentication_failed":
                        self._attr_available = False
                        _LOGGER.error("API key authentication failed")

                    if not transcript_future.done():
                        transcript_future.set_exception(
                            Exception(f"Speechmatics error: {error_msg}")
                        )

                try:
                    await asyncio.wait_for(
                        client.start_session(
                            transcription_config=transcription_config,
                            audio_format=audio_format,
                        ),
                        timeout=10.0,
                    )

                    _LOGGER.debug("Session started, streaming audio...")

                    async for chunk in stream:
                        if chunk:
                            await client.send_audio(chunk)

                    _LOGGER.debug("Audio stream finished, waiting for final transcript...")

                    try:
                        await asyncio.wait_for(transcript_future, timeout=10.0)
                    except asyncio.TimeoutError:
                        _LOGGER.warning("Timeout waiting for final transcript")
                        result_state = SpeechResultState.ERROR
                        error_message = "Timeout waiting for transcription"

                except Exception as e:
                    _LOGGER.error("Error during audio streaming: %s", e)
                    result_state = SpeechResultState.ERROR
                    error_message = str(e)
                    if not transcript_future.done():
                        transcript_future.cancel()

        except asyncio.TimeoutError as e:
            _LOGGER.error("Timeout connecting to Speechmatics API: %s", e)
            result_state = SpeechResultState.ERROR
            error_message = "Connection timeout"
            self._attr_available = False
        except ConnectionError as e:
            _LOGGER.error("Connection error: %s", e)
            result_state = SpeechResultState.ERROR
            error_message = f"Connection error: {str(e)}"
            self._attr_available = False
        except ValueError as e:
            _LOGGER.error("Invalid configuration: %s", e)
            result_state = SpeechResultState.ERROR
            error_message = f"Invalid configuration: {str(e)}"
        except Exception as e:
            _LOGGER.error("Error in async_process_audio_stream: %s", e, exc_info=True)
            result_state = SpeechResultState.ERROR
            error_message = str(e)

        final_text = " ".join(transcript_parts).strip()

        if not final_text and result_state == SpeechResultState.SUCCESS:
            result_state = SpeechResultState.ERROR
            error_message = "No transcription received"

        _LOGGER.debug(
            "Transcription result: text='%s', state=%s, error=%s",
            final_text,
            result_state,
            error_message,
        )

        if error_message:
            _LOGGER.error("STT error: %s", error_message)
        
        return SpeechResult(
            text=final_text,
            result=result_state,
        )
