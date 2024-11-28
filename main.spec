# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main.py'],
             binaries=[],
             datas=[('src', 'src/'), ('settings.yaml', 'lib/')],
             hiddenimports=['vtkmodules', 'vtkmodules.all', 'vtkmodules.qt.QVTKRenderWindowInteractor', 'vtkmodules.util', 'vtkmodules.util.numpy_support', 'vtkmodules.util.data_model', 'yaml', 'numpy', 'pkg_resources.extern'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='FASP',
          debug=True,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False)
