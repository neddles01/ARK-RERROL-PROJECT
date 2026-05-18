import time
import pyautogui
import asyncio
from ocr_engine import OcrManager
from analyzer import analyze_text

class RerollEngine:
    def __init__(self, item_click_coords: tuple, reroll_button_coords: tuple, 
                 ocr_region: dict, target_stats: list, item_type: str, 
                 max_attempts: int = 500, click_delay: float = 0.8):
        """
        Engine responsável por automatizar o ciclo de Reroll do ARK.
        
        :param item_click_coords: (x, y) posição do item na tela
        :param reroll_button_coords: (x, y) posição do botão de reroll
        :param ocr_region: dict contendo top, left, width, height (área geral do OCR)
        :param target_stats: lista de dicts com {"stat_name": str, "min_value": float}
        :param item_type: string identificando o tipo do item
        :param max_attempts: limite máximo de tentativas
        :param click_delay: tempo de espera após cliques
        """
        self.item_click_coords = item_click_coords
        self.reroll_button_coords = reroll_button_coords
        self.ocr_region = ocr_region
        self.target_stats = target_stats
        self.item_type = item_type
        self.max_attempts = max_attempts
        self.click_delay = click_delay
        
        self._is_running = False
        self.ocr_manager = OcrManager()

    def stop(self):
        """Sinaliza para a engine parar o loop."""
        self._is_running = False

    def run(self, on_progress=None) -> dict:
        """
        Executa o loop de automação do reroll.
        """
        self._is_running = True
        attempt = 0
        
        x = self.ocr_region["left"]
        y = self.ocr_region["top"]
        w = self.ocr_region["width"]
        h = self.ocr_region["height"]

        while self._is_running and attempt < self.max_attempts:
            attempt += 1
            
            try:
                # 1. Clica no item para abrir o tooltip
                pyautogui.click(self.item_click_coords[0], self.item_click_coords[1])
                
                # 2. Aguarda delay fixo de 1 segundo para o tooltip renderizar
                time.sleep(1.0)
                
                # 3 & 4. Captura a área geral onde o tooltip aparece e roda o OCR
                result_text = asyncio.run(self.ocr_manager.capture_and_recognize(x, y, w, h))
                
                # 5. Passa o texto para o analyzer.py
                all_approved = True
                current_stats = {}
                
                for target in self.target_stats:
                    stat_name = target["stat_name"]
                    min_val = target["min_value"]
                    
                    analysis = analyze_text(result_text, self.item_type, stat_name, min_val)
                    current_stats[stat_name] = analysis
                    
                    if not analysis["approved"]:
                        all_approved = False
                
                if on_progress:
                    on_progress(attempt, current_stats)

                # 6. Se aprovado: para
                if all_approved:
                    self._is_running = False
                    return {
                        "success": True, 
                        "attempts": attempt, 
                        "found_stats": current_stats
                    }
                    
                # 7. Se reprovado: clica em reroll, aguarda click_delay e repete o loop
                pyautogui.click(self.reroll_button_coords[0], self.reroll_button_coords[1])
                time.sleep(self.click_delay)
                
            except Exception as e:
                print(f"[RerollEngine] Erro na tentativa {attempt}: {e}")
                if on_progress:
                    on_progress(attempt, {"error": str(e)})
                
                time.sleep(self.click_delay)
                continue

        self._is_running = False
        return {
            "success": False, 
            "attempts": attempt
        }
