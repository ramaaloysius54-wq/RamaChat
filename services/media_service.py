from pathlib import Path
from config.settings import BASE_DIR

class MediaService:
    @staticmethod
    def compress_image(input_path: str, max_width: int = 1280, quality: int = 80) -> str:
        from PIL import Image
        src = Path(input_path)
        out_dir = BASE_DIR / "database" / "tmp_media"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"compressed_{src.stem}.jpg"
        with Image.open(src) as img:
            img = img.convert("RGB")
            if img.width > max_width:
                ratio = max_width / float(img.width)
                img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
            img.save(out_path, "JPEG", optimize=True, quality=quality)
        return str(out_path)

    @staticmethod
    def pick_file(on_selection: callable, filters: list[str] | None = None) -> None:
        from plyer import filechooser
        filechooser.open_file(on_selection=on_selection, filters=filters or ["*.*"])
