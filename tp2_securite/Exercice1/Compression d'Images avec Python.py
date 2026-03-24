"""
Exercice 1.1 - Compression d'Images JPEG avec différents niveaux de qualité
Bibliothèque requise : pip install Pillow
"""

from PIL import Image
import os

def compress_image_jpeg(input_path, output_dir, quality_levels=[10, 30, 50, 70, 90]):
    """
    Compresse une image en JPEG avec différents niveaux de qualité.
    
    :param input_path: Chemin vers l'image d'entrée
    :param output_dir: Dossier de sortie
    :param quality_levels: Liste des niveaux de qualité (1-95)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Ouvrir l'image originale
    img = Image.open(input_path).convert("RGB")
    original_size = os.path.getsize(input_path)
    filename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"Image originale : {input_path}")
    print(f"Taille originale : {original_size / 1024:.2f} Ko")
    print(f"Dimensions : {img.size[0]}x{img.size[1]} pixels")
    print("-" * 55)
    print(f"{'Qualité':<10} {'Taille (Ko)':<15} {'Réduction (%)':<15}")
    print("-" * 55)

    results = []

    for quality in quality_levels:
        output_path = os.path.join(output_dir, f"{filename}_q{quality}.jpg")
        img.save(output_path, format="JPEG", quality=quality, optimize=True)
        
        compressed_size = os.path.getsize(output_path)
        reduction = (1 - compressed_size / original_size) * 100

        print(f"{quality:<10} {compressed_size / 1024:<15.2f} {reduction:<15.1f}")
        results.append({
            "quality": quality,
            "path": output_path,
            "size_kb": compressed_size / 1024,
            "reduction_pct": reduction
        })

    print("-" * 55)
    print(f"\nImages compressées sauvegardées dans : {output_dir}")
    return results


# ──────────────────────────────────────────────
# UTILISATION — modifiez le chemin ci-dessous
# ──────────────────────────────────────────────
if __name__ == "__main__":
    INPUT_IMAGE = "image.png"          # ← chemin vers votre image d'entrée
    OUTPUT_DIR  = "compressed_images"  # ← dossier de sortie

    if not os.path.exists(INPUT_IMAGE):
        # Créer une image de test si aucune image n'est fournie
        print("Aucune image fournie — création d'une image de test (512x512)...")
        test_img = Image.new("RGB", (512, 512), color=(100, 149, 237))
        # Dégradé simple pour simuler du contenu réel
        pixels = test_img.load()
        for i in range(512):
            for j in range(512):
                pixels[i, j] = (i % 256, j % 256, (i + j) % 256)
        INPUT_IMAGE = "test_image.jpg"
        test_img.save(INPUT_IMAGE, quality=95)
        print(f"Image de test créée : {INPUT_IMAGE}\n")

    compress_image_jpeg(INPUT_IMAGE, OUTPUT_DIR)
