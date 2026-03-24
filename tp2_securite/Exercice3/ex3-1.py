"""
Exercice 3.1 - Compression Vidéo avec H.264
Bibliothèques requises :
    pip install moviepy
    + ffmpeg installé sur le système (déjà fait ✅)
"""

from moviepy import VideoFileClip
import os
import time


def compress_video_h264(input_path, output_path=None, crf=23):
    """
    Compresse une vidéo en H.264 via MoviePy.

    :param input_path:  Chemin de la vidéo source
    :param output_path: Chemin de la vidéo compressée (optionnel)
    :param crf:         Qualité H.264 (0=parfait, 51=pire, 23=défaut)
    """
    if not os.path.exists(input_path):
        print(f"[ERREUR] Fichier introuvable : {input_path}")
        return

    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_h264_crf{crf}.mp4"

    # Charger la vidéo
    clip = VideoFileClip(input_path)
    original_size = os.path.getsize(input_path)

    print(f"\nVidéo source     : {input_path}")
    print(f"Durée            : {clip.duration:.2f} secondes")
    print(f"Résolution       : {clip.size[0]}x{clip.size[1]} px")
    print(f"FPS              : {clip.fps}")
    print(f"Taille originale : {original_size / (1024*1024):.2f} Mo")
    print(f"\nCompression H.264 (CRF={crf}) en cours...")

    t0 = time.time()
    clip.write_videofile(
        output_path,
        codec="libx264",
        ffmpeg_params=["-crf", str(crf)],
        logger=None  # Masquer les logs de MoviePy
    )
    elapsed = time.time() - t0
    clip.close()

    comp_size = os.path.getsize(output_path)
    reduction = (1 - comp_size / original_size) * 100

    print(f"\n✅ Compression terminée en {elapsed:.1f}s")
    print(f"Taille compressée : {comp_size / (1024*1024):.2f} Mo")
    print(f"Réduction         : {reduction:.1f}%")
    print(f"Fichier créé      : {output_path}")

    return output_path


# ──────────────────────────────────────────────
# UTILISATION
# ──────────────────────────────────────────────
if __name__ == "__main__":
    INPUT_VIDEO = "video.mp4"   # ← chemin vers votre vidéo

    compress_video_h264(INPUT_VIDEO, crf=23)
