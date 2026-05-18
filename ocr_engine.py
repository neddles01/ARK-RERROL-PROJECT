import mss
from PIL import Image
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat, BitmapAlphaMode
from winsdk.windows.security.cryptography import CryptographicBuffer

class OcrManager:
    def __init__(self):
        self.engine = OcrEngine.try_create_from_user_profile_languages()
        if not self.engine:
            raise RuntimeError("Falha ao inicializar o Windows OCR com os idiomas do perfil do usuário.")

    async def capture_and_recognize(self, x: int, y: int, width: int, height: int) -> str:
        """
        Captures a screen region and performs OCR on it.
        """
        monitor = {"top": y, "left": x, "width": width, "height": height}
        
        with mss.MSS() as sct:
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img = img.convert("RGBA")
            
            # Convert bytes to IBuffer
            buffer = CryptographicBuffer.create_from_byte_array(bytearray(img.tobytes()))
            
            # Create SoftwareBitmap
            sb = SoftwareBitmap.create_copy_from_buffer(
                buffer, 
                BitmapPixelFormat.RGBA8, 
                img.width, 
                img.height, 
                BitmapAlphaMode.PREMULTIPLIED
            )
            
            # Recognize text asynchronously
            result = await self.engine.recognize_async(sb)
            
            # Força a extração de cada linha individualmente
            lines_text = []
            for line in result.lines:
                lines_text.append(line.text)
                
            return "\n".join(lines_text)
