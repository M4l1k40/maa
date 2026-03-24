"""
Exercice 1.2 - Comparaison des méthodes de compression : JPEG, PNG, GIF
Bibliothèques requises : pip install Pillow
"""

from PIL import Image
import os
import time

# ──────────────────────────────────────────────────────────
# Méthodes de compression à comparer
# ──────────────────────────────────────────────────────────
FORMATS = {
    "JPEG": {"ext": ".jpg",  "params": {"quality": 85, "optimize": True}},
    "PNG":  {"ext": ".png",  "params": {"optimize": True, "compress_level": 6}},
    "GIF":  {"ext": ".gif",  "params": {}},
}


def compare_compression(input_path, output_dir="comparison_output"):
    """Compare JPEG, PNG et GIF sur une même image."""
    os.makedirs(output_dir, exist_ok=True)

    img = Image.open(input_path).convert("RGB")
    original_size = os.path.getsize(input_path)
    filename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"\n{'='*65}")
    print(f"Image : {input_path}  ({img.size[0]}x{img.size[1]} px)")
    print(f"Taille originale : {original_size / 1024:.2f} Ko")
    print(f"{'='*65}")
    print(f"{'Format':<8} {'Taille (Ko)':<14} {'Réduction (%)':<16} {'Temps (ms)':<12}")
    print(f"{'-'*65}")

    results = []

    for fmt, cfg in FORMATS.items():
        output_path = os.path.join(output_dir, f"{filename}_{fmt}{cfg['ext']}")

        # GIF nécessite une conversion en mode P (palette 256 couleurs)
        save_img = img.convert("P", palette=Image.ADAPTIVE) if fmt == "GIF" else img

        t0 = time.time()
        save_img.save(output_path, format=fmt, **cfg["params"])
        elapsed_ms = (time.time() - t0) * 1000

        comp_size = os.path.getsize(output_path)
        reduction = (1 - comp_size / original_size) * 100

        print(f"{fmt:<8} {comp_size/1024:<14.2f} {reduction:<16.1f} {elapsed_ms:<12.1f}")
        results.append({
            "format": fmt,
            "path": output_path,
            "size_kb": comp_size / 1024,
            "reduction_pct": reduction,
            "time_ms": elapsed_ms
        })

    print(f"{'='*65}")
    return results


def run_on_multiple_images(image_paths):
    """Lance la comparaison sur plusieurs images et affiche un résumé."""
    all_results = {}
    for path in image_paths:
        if os.path.exists(path):
            all_results[path] = compare_compression(path)
        else:
            print(f"[AVERTISSEMENT] Image introuvable : {path}")

    # ── Conclusion globale ──────────────────────────────────
    print("\n" + "="*65)
    print("CONCLUSION - Analyse comparative des méthodes de compression")
    print("="*65)
    print("""
  JPEG :
    ✔ Meilleure réduction de taille pour les photos (50-90 %)
    ✔ Compression rapide
    ✘ Compression avec pertes (artefacts à faible qualité)
    ➜ Idéal pour : photographies, images naturelles

  PNG :
    ✔ Compression sans pertes — qualité parfaite conservée
    ✔ Supporte la transparence (canal alpha)
    ✘ Fichiers plus grands que JPEG pour les photos
    ➜ Idéal pour : logos, illustrations, captures d'écran

  GIF :
    ✔ Supporte les animations
    ✘ Limité à 256 couleurs — dégradation visible sur photos
    ✘ Taille souvent supérieure à JPEG
    ➜ Idéal pour : icônes simples, animations légères

  → Pour les photos     : JPEG (qualité 70-85) offre le meilleur compromis
  → Pour la précision   : PNG garantit 0 perte de qualité
  → Pour les animations : GIF reste le standard historique (WebP le remplace)
""")


# ──────────────────────────────────────────────
# UTILISATION
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Créer des images de test si nécessaire
    test_images = [
        "image.png",   # ← ton image ici
        "chemin/vers/image2.jpg",      # ← optionnel, tu peux en mettre plusieurs
    ]
    run_on_multiple_images(test_images)
