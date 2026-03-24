"""
Exercice 3.2 - Comparaison des codecs vidéo : H.264 vs VP9
Bibliothèques requises :
    pip install moviepy
    + ffmpeg installé sur le système (déjà fait ✅)
"""

from moviepy import VideoFileClip
import os
import time


# ── Configuration des codecs à comparer ────────────────────
CODECS = {
    "H.264": {
        "codec":         "libx264",
        "output_ext":    ".mp4",
        "ffmpeg_params": ["-crf", "23", "-preset", "medium"],
        "description":   "Standard universel, compatible partout"
    },
    "VP9": {
        "codec":         "libvpx-vp9",
        "output_ext":    ".webm",
        "ffmpeg_params": ["-crf", "33", "-b:v", "0"],
        "description":   "Codec Google, meilleure compression mais plus lent"
    },
}


def compare_codecs(input_path, output_dir="video_compressed"):
    """
    Compare H.264 et VP9 sur la même vidéo.

    :param input_path: Chemin de la vidéo source
    :param output_dir: Dossier de sortie
    """
    if not os.path.exists(input_path):
        print(f"[ERREUR] Fichier introuvable : {input_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    clip = VideoFileClip(input_path)
    original_size = os.path.getsize(input_path)
    filename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"\n{'='*65}")
    print(f"Vidéo source     : {input_path}")
    print(f"Durée            : {clip.duration:.2f} s")
    print(f"Résolution       : {clip.size[0]}x{clip.size[1]} px")
    print(f"FPS              : {clip.fps}")
    print(f"Taille originale : {original_size / (1024*1024):.2f} Mo")
    print(f"{'='*65}")
    print(f"{'Codec':<10} {'Taille (Mo)':<14} {'Réduction(%)':<15} {'Temps(s)':<12} Format")
    print(f"{'-'*65}")

    results = []

    for codec_name, cfg in CODECS.items():
        output_path = os.path.join(output_dir, f"{filename}_{codec_name}{cfg['output_ext']}")

        print(f"\n⏳ Encodage {codec_name}...")
        t0 = time.time()

        try:
            clip.write_videofile(
                output_path,
                codec=cfg["codec"],
                ffmpeg_params=cfg["ffmpeg_params"],
                logger=None
            )
            elapsed = time.time() - t0

            comp_size = os.path.getsize(output_path)
            reduction = (1 - comp_size / original_size) * 100

            print(f"{codec_name:<10} {comp_size/(1024*1024):<14.2f} {reduction:<15.1f} {elapsed:<12.1f} {cfg['output_ext']}")

            results.append({
                "codec":        codec_name,
                "size_mb":      comp_size / (1024 * 1024),
                "reduction":    reduction,
                "time_s":       elapsed,
                "path":         output_path,
                "description":  cfg["description"]
            })

        except Exception as e:
            print(f"[ERREUR] {codec_name} : {e}")

    clip.close()

    print(f"\n{'='*65}")
    print_conclusion(results)
    return results


def print_conclusion(results):
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           ANALYSE — Comparaison des codecs vidéo                ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  H.264 (libx264) :                                               ║
║    ✔ Compatible avec tous les appareils et navigateurs           ║
║    ✔ Encodage rapide                                             ║
║    ✔ Excellente qualité visuelle                                 ║
║    ✘ Compression légèrement inférieure à VP9                     ║
║    ➜ Usage : streaming, partage universel, YouTube               ║
║                                                                  ║
║  VP9 (libvpx-vp9) :                                              ║
║    ✔ Meilleure compression (fichiers 30-50% plus petits)         ║
║    ✔ Qualité visuelle supérieure à même taille                   ║
║    ✘ Encodage beaucoup plus lent                                 ║
║    ✘ Moins compatible (nécessite navigateur moderne)             ║
║    ➜ Usage : YouTube 4K, streaming web (WebM)                    ║
║                                                                  ║
║  → Pour usage général    : H.264 (rapidité + compatibilité)     ║
║  → Pour taille optimale  : VP9 (si le temps d'encodage le       ║
║                            permet)                               ║
╚══════════════════════════════════════════════════════════════════╝
""")


# ──────────────────────────────────────────────
# UTILISATION
# ──────────────────────────────────────────────
if __name__ == "__main__":
    INPUT_VIDEO = "video.mp4"   # ← chemin vers votre vidéo

    compare_codecs(INPUT_VIDEO)
