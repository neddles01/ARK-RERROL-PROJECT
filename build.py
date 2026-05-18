import os
import sys
import subprocess
import shutil
from datetime import datetime
import glob

def install_dependencies():
    print("Verificando/instalando dependências (Nuitka, ordered-set, zstandard)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka", "ordered-set", "zstandard"])
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
        sys.exit(1)

def backup_source_files():
    print("Criando backup dos arquivos fonte...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join("backup_src", f"backup_{timestamp}")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    py_files = glob.glob("*.py")
    for file in py_files:
        # Não fazer backup do próprio build.py se não quiser, mas vamos fazer de tudo.
        shutil.copy2(file, backup_dir)
        
    print(f"Backup concluído em: {backup_dir}")

def run_nuitka_build():
    print("Iniciando compilação com Nuitka...")
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--windowed",
        "--enable-plugin=pyqt6",
        "--output-dir=dist",
        "--output-filename=ARKReroll.exe",
        "--remove-output"
    ]
    
    if os.path.exists("last_config.json"):
        cmd.append("--include-data-files=last_config.json=last_config.json")
    else:
        print("Aviso: last_config.json não encontrado. Ignorando inclusão no build.")
        
    cmd.append("main.py")
    
    try:
        subprocess.check_call(cmd)
        print("\n=======================================================")
        print("Build concluído! Executável em: dist/ARKReroll.exe")
        print("=======================================================\n")
    except subprocess.CalledProcessError as e:
        print(f"\nErro durante a compilação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_dependencies()
    backup_source_files()
    run_nuitka_build()
