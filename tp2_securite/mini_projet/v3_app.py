"""
Mini-Projet : Application de Streaming Multimédia — Backend complet v3
Compression + Codage : Images, Audio, Vidéo + Téléchargement
QoS + Sécurité
pip install flask flask-limiter flask-cors pillow pydub cryptography soundfile
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image
from cryptography.fernet import Fernet
import os, time, json, io, base64, subprocess
from datetime import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# ── Sécurité ────────────────────────────────────────────
SECRET_KEY = Fernet.generate_key()
cipher     = Fernet(SECRET_KEY)
VALID_TOKENS = {"admin-token-2026", "student-token-2026"}

limiter = Limiter(
    get_remote_address, app=app,
    default_limits=["100 per minute"],
    storage_uri="memory://"
)

# ── Dossiers ────────────────────────────────────────────
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
LOG_FILE   = "stream_log.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Stats ───────────────────────────────────────────────
stats = {"images": 0, "audio": 0, "video": 0, "saved_mb": 0.0, "errors": 0}

# ── Helpers ─────────────────────────────────────────────
def log_event(etype, details):
    entry = {"timestamp": datetime.now().isoformat(), "event": etype, "details": details}
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE) as f: logs = json.load(f)
        except: pass
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs[-200:], f, indent=2)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Auth-Token", "")
        if token not in VALID_TOKENS:
            log_event("AUTH_FAILED", {"ip": request.remote_addr})
            stats["errors"] += 1
            return jsonify({"error": "Non autorisé"}), 401
        return f(*args, **kwargs)
    return decorated

def find_ffmpeg():
    paths = ["ffmpeg", r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"]
    for p in paths:
        try:
            r = subprocess.run([p, "-version"], capture_output=True, timeout=2)
            if r.returncode == 0: return p
        except: pass
    return None

def get_audio_info(filepath):
    """Récupère les infos audio avec ffprobe"""
    try:
        cmd = [FFMPEG.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            stream = data["streams"][0] if data.get("streams") else {}
            return {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "channels": stream.get("channels", 2),
                "sample_rate": stream.get("sample_rate", 44100)
            }
    except: pass
    return {"duration": 0, "channels": 2, "sample_rate": 44100}

def convert_audio_ffmpeg(input_path, output_path, bitrate="128k", fmt="mp3"):
    """Convertit audio avec ffmpeg"""
    try:
        cmd = [FFMPEG, "-i", input_path, "-b:a", bitrate, "-acodec", "libmp3lame" if fmt=="mp3" else fmt]
        cmd += ["-y", output_path]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
    except: return False

FFMPEG = find_ffmpeg()

# ════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════
@app.route("/")
def dashboard():
    """Servir le fichier HTML du dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "v3_dashboard.html")
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path, mimetype="text/html")
    return jsonify({"error": "Dashboard non trouvé"}), 404

# ════════════════════════════════════════════════════════
# STATUT
# ════════════════════════════════════════════════════════
@app.route("/api/status")
def status():
    return jsonify({
        "status": "online", "ffmpeg": FFMPEG is not None,
        "stats": stats,
        "security": {"auth": "Token Bearer", "encryption": "Fernet AES-128", "rate_limit": "100/min"}
    })

@app.route("/api/logs")
@require_auth
def get_logs():
    if not os.path.exists(LOG_FILE): return jsonify([])
    try:
        with open(LOG_FILE) as f: return jsonify(json.load(f))
    except: return jsonify([])

@app.route("/api/qos")
@require_auth
def qos():
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE) as f: logs = json.load(f)
        except: pass
    times = [l["details"].get("time_ms", 0) for l in logs if "time_ms" in l.get("details", {})]
    return jsonify({
        "avg_latency_ms": round(sum(times)/len(times), 1) if times else 0,
        "total_requests": len(logs),
        "auth_failures":  sum(1 for l in logs if l["event"] == "AUTH_FAILED"),
        "stats": stats
    })

# ════════════════════════════════════════════════════════
# TÉLÉCHARGEMENT des fichiers compressés
# ════════════════════════════════════════════════════════
@app.route("/api/download/<filename>")
@require_auth
def download_file(filename):
    """Télécharge un fichier compressé depuis le dossier outputs."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Fichier introuvable"}), 404
    # Sécurité : empêcher path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"error": "Nom de fichier invalide"}), 400
    return send_file(filepath, as_attachment=True, download_name=filename)

# ════════════════════════════════════════════════════════
# IMAGE
# ════════════════════════════════════════════════════════
CODEC_IMAGE = {
    "JPEG": {"codec": "JPEG (DCT)", "type": "Avec pertes", "standard": "ISO/IEC 10918", "espace": "YCbCr"},
    "PNG":  {"codec": "PNG (DEFLATE)", "type": "Sans pertes", "standard": "ISO/IEC 15948", "espace": "RGB/RGBA"},
    "GIF":  {"codec": "GIF (LZW)", "type": "Sans pertes", "standard": "GIF89a", "couleurs": "Max 256"},
    "WEBP": {"codec": "WebP (VP8)", "type": "Avec/Sans pertes", "standard": "Google RFC 6386", "gain": "~30% vs JPEG"},
}

@app.route("/api/image/compress", methods=["POST"])
@require_auth
@limiter.limit("30 per minute")
def compress_image():
    t0 = time.time()
    if "file" not in request.files:
        return jsonify({"error": "Fichier manquant"}), 400

    file    = request.files["file"]
    quality = int(request.form.get("quality", 75))
    fmt     = request.form.get("format", "JPEG").upper()

    raw  = file.read()
    orig = len(raw)
    fname_base = os.path.splitext(file.filename)[0] if file.filename else "image"
    ext_map = {"JPEG": "jpg", "PNG": "png", "GIF": "gif", "WEBP": "webp"}
    out_filename = f"{fname_base}_compressed.{ext_map.get(fmt,'jpg')}"
    out_path = os.path.join(OUTPUT_DIR, out_filename)

    try:
        img = Image.open(io.BytesIO(raw))
        img_rgb = img.convert("RGB")
        out = io.BytesIO()

        if fmt == "JPEG":
            img_rgb.save(out, "JPEG", quality=quality, optimize=True)
            img_rgb.save(out_path, "JPEG", quality=quality, optimize=True)
        elif fmt == "PNG":
            img.save(out, "PNG", optimize=True)
            img.save(out_path, "PNG", optimize=True)
        elif fmt == "GIF":
            gif = img.convert("P", palette=Image.ADAPTIVE, colors=256)
            gif.save(out, "GIF")
            gif.save(out_path, "GIF")
        elif fmt == "WEBP":
            img_rgb.save(out, "WEBP", quality=quality)
            img_rgb.save(out_path, "WEBP", quality=quality)

        comp = out.tell()
        reduction = (1 - comp / orig) * 100
        stats["images"] += 1
        stats["saved_mb"] += max(0, (orig - comp)) / 1e6

        # Preview base64
        out.seek(0)
        preview = base64.b64encode(out.read()).decode()
        mime = {"JPEG":"jpeg","PNG":"png","GIF":"gif","WEBP":"webp"}.get(fmt,"jpeg")

        log_event("IMAGE_COMPRESS", {
            "format": fmt, "quality": quality,
            "original_kb": round(orig/1024,1),
            "compressed_kb": round(comp/1024,1),
            "reduction": f"{reduction:.1f}%",
            "time_ms": round((time.time()-t0)*1000,1)
        })

        return jsonify({
            "success": True,
            "original_kb":   round(orig/1024, 2),
            "compressed_kb": round(comp/1024, 2),
            "reduction_pct": round(reduction, 1),
            "dimensions":    f"{img.size[0]}x{img.size[1]}",
            "time_ms":       round((time.time()-t0)*1000, 1),
            "codec_info":    CODEC_IMAGE.get(fmt, {}),
            "preview":       f"data:image/{mime};base64,{preview}",
            "download_file": out_filename,
        })
    except Exception as e:
        stats["errors"] += 1
        return jsonify({"error": str(e)}), 500

# ════════════════════════════════════════════════════════
# AUDIO
# ════════════════════════════════════════════════════════
CODEC_AUDIO = {
    "mp3":  {"codec": "MP3 (MPEG Layer III)", "type": "Avec pertes", "algo": "MDCT + psychoacoustique", "standard": "ISO/IEC 11172-3"},
    "ogg":  {"codec": "OGG Vorbis", "type": "Avec pertes", "algo": "MDCT + codage entropique", "standard": "Xiph.Org"},
    "flac": {"codec": "FLAC", "type": "Sans pertes", "algo": "Prédiction linéaire + Rice", "standard": "Xiph.Org"},
}

@app.route("/api/audio/compress", methods=["POST"])
@require_auth
@limiter.limit("20 per minute")
def compress_audio():
    t0 = time.time()
    if not FFMPEG:
        return jsonify({"error": "FFmpeg non disponible"}), 503
    if "file" not in request.files:
        return jsonify({"error": "Fichier manquant"}), 400

    file    = request.files["file"]
    bitrate = request.form.get("bitrate", "128k")
    fmt     = request.form.get("format", "mp3").lower()

    fname_base = os.path.splitext(file.filename)[0] if file.filename else "audio"
    out_filename = f"{fname_base}_compressed.{fmt}"
    tmp_in   = os.path.join(UPLOAD_DIR, f"in_{int(time.time())}.wav")
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    file.save(tmp_in)
    orig = os.path.getsize(tmp_in)

    try:
        success = convert_audio_ffmpeg(tmp_in, out_path, bitrate, fmt)
        if not success:
            return jsonify({"error": "Erreur conversion audio"}), 500
        
        info = get_audio_info(tmp_in)

        comp = os.path.getsize(out_path)
        reduction = (1 - comp / orig) * 100
        stats["audio"] += 1
        stats["saved_mb"] += max(0, (orig - comp)) / 1e6

        log_event("AUDIO_COMPRESS", {
            "format": fmt, "bitrate": bitrate,
            "duration_s": round(info["duration"],1),
            "original_kb": round(orig/1024,1),
            "compressed_kb": round(comp/1024,1),
            "reduction": f"{reduction:.1f}%",
            "time_ms": round((time.time()-t0)*1000,1)
        })

        return jsonify({
            "success":       True,
            "original_kb":   round(orig/1024, 2),
            "compressed_kb": round(comp/1024, 2),
            "reduction_pct": round(reduction, 1),
            "duration_s":    round(info["duration"], 2),
            "channels":      info["channels"],
            "sample_rate":   info["sample_rate"],
            "time_ms":       round((time.time()-t0)*1000, 1),
            "codec_info":    CODEC_AUDIO.get(fmt, {}),
            "download_file": out_filename,
        })
    except Exception as e:
        stats["errors"] += 1
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_in): os.remove(tmp_in)

# ════════════════════════════════════════════════════════
# VIDÉO
# ════════════════════════════════════════════════════════
CODEC_VIDEO = {
    "h264": {"codec": "H.264 / AVC", "lib": "libx264", "ext": "mp4",  "type": "Avec pertes", "standard": "ISO/IEC 14496-10", "usage": "Streaming universel"},
    "h265": {"codec": "H.265 / HEVC","lib": "libx265", "ext": "mp4",  "type": "Avec pertes", "standard": "ISO/IEC 23008-2",  "usage": "4K/8K, 50% plus efficace"},
    "vp9":  {"codec": "VP9",          "lib": "libvpx-vp9","ext":"webm","type": "Avec pertes", "standard": "Google/IETF",      "usage": "YouTube 4K, web"},
}

@app.route("/api/video/compress", methods=["POST"])
@require_auth
@limiter.limit("5 per minute")
def compress_video():
    t0 = time.time()
    if not FFMPEG:
        return jsonify({"error": "FFmpeg non trouvé"}), 500
    if "file" not in request.files:
        return jsonify({"error": "Fichier manquant"}), 400

    file  = request.files["file"]
    codec = request.form.get("codec", "h264")
    crf   = request.form.get("crf", "23")
    cfg   = CODEC_VIDEO.get(codec, CODEC_VIDEO["h264"])

    fname_base   = os.path.splitext(file.filename)[0] if file.filename else "video"
    out_filename = f"{fname_base}_compressed_{codec}.{cfg['ext']}"
    tmp_in   = os.path.join(UPLOAD_DIR, f"vin_{int(time.time())}.mp4")
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    file.save(tmp_in)
    orig = os.path.getsize(tmp_in)

    try:
        if codec == "vp9":
            cmd = [FFMPEG, "-i", tmp_in, "-c:v", "libvpx-vp9",
                   "-crf", crf, "-b:v", "0", "-c:a", "libopus", "-y", out_path]
        else:
            cmd = [FFMPEG, "-i", tmp_in, "-c:v", cfg["lib"],
                   "-crf", crf, "-preset", "fast", "-c:a", "aac", "-b:a", "128k", "-y", out_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0 or not os.path.exists(out_path):
            return jsonify({"error": "Encodage échoué", "details": result.stderr[-300:]}), 500

        comp = os.path.getsize(out_path)
        reduction = (1 - comp / orig) * 100
        elapsed = round((time.time()-t0)*1000, 1)
        stats["video"] += 1
        stats["saved_mb"] += max(0, (orig - comp)) / 1e6

        log_event("VIDEO_COMPRESS", {
            "codec": codec, "crf": crf,
            "original_mb": round(orig/1e6,2),
            "compressed_mb": round(comp/1e6,2),
            "reduction": f"{reduction:.1f}%",
            "time_ms": elapsed
        })

        return jsonify({
            "success":       True,
            "codec":         codec,
            "original_mb":   round(orig/1e6, 2),
            "compressed_mb": round(comp/1e6, 2),
            "reduction_pct": round(reduction, 1),
            "time_ms":       elapsed,
            "codec_info":    cfg,
            "download_file": out_filename,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout — vidéo trop longue"}), 500
    except Exception as e:
        stats["errors"] += 1
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_in): os.remove(tmp_in)

if __name__ == "__main__":
    print("\n" + "═"*50)
    print("  StreamMedia Pro — Backend v3")
    print(f"  FFmpeg : {'✅ Trouvé' if FFMPEG else '❌ Non trouvé'}")
    print("  URL    : http://localhost:5000")
    print("  Token  : admin-token-2026")
    print("═"*50 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
