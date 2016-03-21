#------------------------------------------------------------------------------------
# build.py
# - This file will compile the Python code into an EXE and then into a neat ZIP file.
#------------------------------------------------------------------------------------

# Imports
import os, sys, shutil, subprocess

# Configuration
mod_name = 'instant-start-mod'
version = '1.2'
install_name = mod_name + '-' + version

# Clean up build-related directories before we start to do anything
if os.path.exists('build'):
	shutil.rmtree('build')
if os.path.exists('dist'):
	shutil.rmtree('dist')
if os.path.exists('target'):
	shutil.rmtree('target')

# Compile the py into an exe
if os.path.exists('C:\Python34\Scripts\pyinstaller.exe'):
    subprocess.call(['C:\Python34\Scripts\pyinstaller.exe', '--onefile', '--windowed', '--icon=otherFiles/options.ico', 'instant-start-mod.py'])
    # 
else:
    print('Error: Edit this file and specify the path to your pyinstaller.exe file.')
    sys.exit(1)

# Make the installation directory inside the "target" directory
install_directory = os.path.join('target', install_name)
shutil.copytree('dist/', install_directory)

# Copy over necessary files
for file_name in ['README.md', 'options.ini', 'Shortcut to BoIA Resources Folder.lnk']:
	shutil.copy(file_name, os.path.join(install_directory, file_name))
for directory_name in ['gameFiles', 'otherFiles']:
	shutil.copytree(directory_name, os.path.join(install_directory, directory_name))

# Rename README.md to README.txt extension so that noobs are less confused
shutil.move(os.path.join(install_directory, 'README.md'), os.path.join(install_directory, 'README.txt'))

# Make the zip file
shutil.make_archive(os.path.join('target', install_name), 'zip', 'target', install_name + '/')

# Clean up
shutil.rmtree('build')
shutil.rmtree('dist')
os.unlink('instant-start-mod.spec')
