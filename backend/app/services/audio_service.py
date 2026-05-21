def generate_audio_reference(session_id: int, voice: str) -> str:
    return f"browser-speech://session/{session_id}?voice={voice}"
