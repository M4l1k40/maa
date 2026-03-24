"""
Exercice 2.2 - Analyse de la Compression Audio
Compare différents débits binaires (bitrates) pour un même fichier WAV → MP3
Bibliothèques requises :
    pip install pydub
    + ffmpeg installé sur le système
"""

from pydub import AudioSegment
import os
import time


# Débits binaires à comparer
BITRATES = ["32k", "64k", "96k", "128k", "192k", "256k", "320k"]

# Qualité audio perçue associée à chaque bitrate (référence standard)
QUALITY_NOTES = {
    "32k":  "Très faible — voix à peine compréhensible",
    "64k":  "Faible     — acceptable pour la voix",
    "96k":  "Moyenne    — musique dégradée",
    "128k": "Bonne      — standard streaming basique",
    "192k": "Très bonne — streaming courant (Spotify, etc.)",
    "256k": "Excellente — quasi-transparent",
    "320k": "Maximale   — limite audible MP3",
}


def analyze_audio_compression(input_path, output_dir="audio_compressed", bitrates=BITRATES):
    """
    Compresse un fichier WAV en MP3 avec différents débits binaires et compare les résultats.

    :param input_path: Chemin du fichier WAV
    :param output_dir: Dossier de sortie
    :param bitrates:   Liste des débits à tester
    """
    if not os.path.exists(input_path):
        print(f"[ERREUR] Fichier introuvable : {input_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Charger l'audio
    audio = AudioSegment.from_wav(input_path)
    original_size = os.path.getsize(input_path)
    duration_s = len(audio) / 1000
    filename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"\n{'='*75}")
    print(f"Fichier source : {input_path}")
    print(f"Durée : {duration_s:.2f} s  |  Canaux : {audio.channels}  |  Fréquence : {audio.frame_rate} Hz")
    print(f"Taille WAV originale : {original_size / 1024:.2f} Ko")
    print(f"{'='*75}")
    print(f"{'Bitrate':<10} {'Taille (Ko)':<14} {'Réduction(%)':<15} {'Temps(ms)':<12} Qualité perçue")
    print(f"{'-'*75}")

    results = []

    for br in bitrates:
        output_path = os.path.join(output_dir, f"{filename}_{br}.mp3")

        t0 = time.time()
        audio.export(output_path, format="mp3", bitrate=br)
        elapsed_ms = (time.time() - t0) * 1000

        comp_size = os.path.getsize(output_path)
        reduction = (1 - comp_size / original_size) * 100
        note = QUALITY_NOTES.get(br, "—")

        print(f"{br:<10} {comp_size/1024:<14.2f} {reduction:<15.1f} {elapsed_ms:<12.1f} {note}")

        results.append({
            "bitrate": br,
            "size_kb": comp_size / 1024,
            "reduction_pct": reduction,
            "time_ms": elapsed_ms,
            "path": output_path
        })

    print(f"{'='*75}")
    print_conclusion(results, original_size)
    return results


def print_conclusion(results, original_size_bytes):
    """Affiche une analyse des résultats."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║               ANALYSE — Compression Audio MP3                   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Débit faible (32k - 64k) :                                      ║
║    ✔ Réduction maximale de taille (90%+)                         ║
║    ✘ Qualité très dégradée, artefacts audibles                   ║
║    ➜ Usage : podcasts basse qualité, voix uniquement             ║
║                                                                  ║
║  Débit moyen (96k - 128k) :                                      ║
║    ✔ Bon compromis taille / qualité                              ║
║    ✔ Standard pour le streaming audio basique                    ║
║    ➜ Usage : streaming mobile, radio en ligne                    ║
║                                                                  ║
║  Débit élevé (192k - 320k) :                                     ║
║    ✔ Qualité quasi-identique au WAV pour l'oreille humaine       ║
║    ✘ Fichiers plus volumineux                                    ║
║    ➜ Usage : musique haute qualité, distribution professionnelle ║
║                                                                  ║
║  → Recommandation générale : 128k–192k pour un usage courant    ║
╚══════════════════════════════════════════════════════════════════╝
""")


# ──────────────────────────────────────────────
# UTILISATION — modifiez le chemin ci-dessous
# ──────────────────────────────────────────────
if __name__ == "__main__":
    INPUT_WAV = "audio.wav"   # ← chemin vers votre fichier WAV

    analyze_audio_compression(INPUT_WAV)
