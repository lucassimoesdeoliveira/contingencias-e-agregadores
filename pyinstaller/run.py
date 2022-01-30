import PyInstaller.__main__

PyInstaller.__main__.run([
    r'..\gui.py',
    '--onefile',
    '--distpath',
    './dist',
    '--workpath',
    './build',
    '--name',
    'Agregadores - v1.0.1 (jan-2022)',
    '--icon',
    r'..\ui\resources\logo-epe.ico',
    '--windowed'
])