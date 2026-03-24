"""
Exercice 2.1 - Conversion Audio : WAV → MP3
Nécessite : ffmpeg (https://ffmpeg.org/)
  Windows : https://www.gyan.dev/ffmpeg/builds/ (télécharger et ajouter au PATH)
  Ou: choco install ffmpeg  / scoop install ffmpeg
"""

import os
import sys
import subprocess
import json


def convert_wav_to_mp3(input_path, output_path=None, bitrate="192k"):
    """
    Convertit un fichier WAV en MP3 avec ffmpeg.
    
    :param input_path:  Chemin du fichier WAV source
    :param output_path: Chemin du fichier MP3 de sortie (optionnel)
    :param bitrate:     Débit binaire du MP3 (ex: "128k", "192k", "320k")
    """
    if not os.path.exists(input_path):
        print(f"[ERREUR] Fichier introuvable : {input_path}")
        return
    
    # Générer automatiquement le nom de sortie si non fourni
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_{bitrate}.mp3"
    
    print(f"Chargement de : {input_path}")
    
    try:
        import soundfile as sf
        # Lire infos du WAV
        audio_data, sample_rate = sf.read(input_path)
        original_size = os.path.getsize(input_path)
        duration = len(audio_data) / sample_rate if len(audio_data.shape) == 1 else audio_data.shape[0] / sample_rate
        channels = 1 if len(audio_data.shape) == 1 else audio_data.shape[1]
        
        print(f"  Durée         : {duration:.2f} secondes")
        print(f"  Canaux        : {channels} ({'Stéréo' if channels >= 2 else 'Mono'})")
        print(f"  Fréquence     : {sample_rate} Hz")
        print(f"  Taille WAV    : {original_size / 1024:.2f} Ko")
    except Exception as e:
        print(f"  Info : {e}")
        original_size = os.path.getsize(input_path)
        print(f"  Taille WAV    : {original_size / 1024:.2f} Ko")
    
    # Chercher ffmpeg
    ffmpeg_paths = [
        "ffmpeg",  # Depuis PATH
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe"
    ]
    
    ffmpeg_found = None
    for path in ffmpeg_paths:
        try:
            result = subprocess.run([path, "-version"], capture_output=True, timeout=2)
            if result.returncode == 0:
                ffmpeg_found = path
                break
        except:
            pass
    
    if not ffmpeg_found:
        print("\n[ERREUR] ffmpeg non trouvé !")
        print("Téléchargez depuis: https://www.gyan.dev/ffmpeg/builds/")
        print("Ou installez avec: choco install ffmpeg  (si chocolatey est installé)")
        return None
    
    # Convertir avec ffmpeg
    cmd = [ffmpeg_found, '-i', input_path, '-b:a', bitrate, '-y', output_path]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path):
            mp3_size = os.path.getsize(output_path)
            reduction = (1 - mp3_size / original_size) * 100
            print(f"  Taille MP3    : {mp3_size / 1024:.2f} Ko  (bitrate: {bitrate})")
            print(f"  Réduction     : {reduction:.1f}%")
            print(f"  Fichier créé  : {output_path}")
            return output_path
        else:
            print(f"[ERREUR] Conversion échouée")
            if result.stderr:
                print(f"  {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print("[ERREUR] Conversion dépassement du délai")
        return None
    except Exception as e:
        print(f"[ERREUR] {e}")
        return None


# ──────────────────────────────────────────────
# UTILISATION
# ──────────────────────────────────────────────
if __name__ == "__main__":
    INPUT_WAV = "audio.wav"   # ← chemin vers votre fichier WAV

    convert_wav_to_mp3(INPUT_WAV, bitrate="192k")
