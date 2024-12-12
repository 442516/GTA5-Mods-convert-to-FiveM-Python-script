import os
import shutil
import zipfile
import sys
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLineEdit, QLabel, QCheckBox, QMessageBox, QComboBox
from PyQt5.QtCore import Qt
import requests

class MultiFiveMModConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = "zh"  # 默认语言为中文
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.get_text("GTA5 Mods to FiveM Converter - MultiDLC Support", "GTA5 Mods 转 FiveM 资源 - 多DLC支持"))
        self.setGeometry(300, 300, 400, 350)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        vbox = QVBoxLayout(central_widget)

        # 添加语言选择下拉菜单
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.get_text("Chinese", "中文"), "zh")
        self.language_combo.addItem(self.get_text("English", "英文"), "en")
        self.language_combo.currentIndexChanged.connect(self.changeLanguage)
        vbox.addWidget(QLabel(self.get_text("Select Language:", "选择语言：")))
        vbox.addWidget(self.language_combo)

        self.dlc_paths = QLineEdit()
        self.dlc_paths.setPlaceholderText(self.get_text("Enter URLs or click 'Upload' to select DLCs", "输入URL或点击'上传'选择DLC包"))
        vbox.addWidget(self.dlc_paths)
        
        self.upload_btn = QPushButton(self.get_text("Upload DLCs", "上传DLC包"), self)
        self.upload_btn.clicked.connect(self.uploadFiles)
        vbox.addWidget(self.upload_btn)

        self.save_original = QCheckBox(self.get_text("Keep Original Files", "保留原始文件"), self)
        vbox.addWidget(self.save_original)

        self.classify_files = QCheckBox(self.get_text("Classify Files", "分类文件"), self)
        vbox.addWidget(self.classify_files)

        self.classification_method = QComboBox()
        self.classification_method.addItems([self.get_text("By DLC Name", "按DLC名称"),
                                             self.get_text("By Resource Type", "按资源类型分类")])
        vbox.addWidget(self.classification_method)

        self.single_vehicle = QCheckBox(self.get_text("Single Vehicle", "单个车辆"), self)
        vbox.addWidget(self.single_vehicle)

        self.classify_to_folders = QCheckBox(self.get_text("Classify to Folders", "分类到文件夹"), self)
        vbox.addWidget(self.classify_to_folders)

        self.convert_btn = QPushButton(self.get_text("Convert", "转换"), self)
        self.convert_btn.clicked.connect(self.startConversion)
        vbox.addWidget(self.convert_btn)

        self.status_label = QLabel(self.get_text("Ready", "就绪"), self)
        vbox.addWidget(self.status_label)

    def get_text(self, english, chinese):
        return chinese if self.language == "zh" else english

    def changeLanguage(self, index):
        self.language = self.language_combo.itemData(index)
        self.initUI()

    def uploadFiles(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, self.get_text("Select DLC Files", "选择DLC文件"), "", "ZIP Files (*.zip)")
        if file_paths:
            self.dlc_paths.setText(', '.join(file_paths))

    def downloadFile(self, url, save_path):
        try:
            with open(save_path, 'wb') as f:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return save_path
        except Exception as e:
            QMessageBox.critical(self, self.get_text("Error", "错误"), f"{self.get_text('Failed to download file:', '下载文件失败：')} {str(e)}")
            return None

    def create_fxmanifest(self, stream_folder, zip_name):
        manifest_path = os.path.join(stream_folder, 'fxmanifest.lua')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write("fx_version 'cerulean'\n")
            f.write("game 'gta5'\n\n")

            file_types = {
                r'.*\.rpf$': 'VEHICLE_METADATA_FILE',
                r'.*\.dat$': 'AUDIO_SOUNDDATA',
                r'.*\.rel$': 'AUDIO_SOUNDDATA',
                r'.*\.awc$': 'AUDIO_WAVEPACK',
                r'.*\.yft$': 'VEHICLE_METADATA_FILE',
                r'.*handling.*\.meta$': 'HANDLING_FILE',
                r'.*vehiclelayouts.*\.meta$': 'VEHICLE_LAYOUTS_FILE',
                r'.*vehicles.*\.meta$': 'VEHICLE_METADATA_FILE',
                r'.*carcols.*\.meta$': 'CARCOLS_FILE',
                r'.*carvariations.*\.meta$': 'VEHICLE_VARIATION_FILE',
                r'.*unlocks.meta$': 'CONTENT_UNLOCKING_META_FILE',
                r'.*ptfxassetinfo.meta$': 'PTFXASSETINFO_FILE',
                r'.*vehiclemodelsets.meta$': 'AMBIENT_VEHICLE_MODEL_SET_FILE',
                r'.*popcycle.dat$': 'POPSCHED_FILE',
                r'.*popgroups.ymt$': 'FIVEM_LOVES_YOU_341B23A2F0E0F131',
                r'.*dlctext.meta$': 'DLCTEXT_FILE',
                r'.*weaponanimations.meta$': 'WEAPON_ANIMATIONS_FILE',
                r'.*weapons.meta$': 'WEAPONINFO_FILE',
                r'.*gxt2$': 'GXT2',
                r'.*weaponcomponents.meta$': 'WEAPON_COMPONENTS_FILE',
                r'.*weapontypes.meta$': 'WEAPON_TYPES_FILE',
                r'.*weaponarchetypes.meta$': 'WEAPON_ARCHETYPES_FILE',
                r'.*weaponloadout.meta$': 'WEAPON_LOADOUT_FILE',
                r'.*weaponattachments.meta$': 'WEAPON_ATTACHMENTS_FILE',
                r'.*weaponanimationset.meta$': 'WEAPON_ANIMATION_SET_FILE',
                r'.*weaponanimations.meta$': 'WEAPON_ANIMATIONS_FILE',
                r'.*weaponanimations2.meta$': 'WEAPON_ANIMATIONS_FILE2',
                # 可以根据文档链接添加更多数据类型
            }

            files_list = []
            for root, dirs, files in os.walk(stream_folder):
                for file in files:
                    file_path = os.path.relpath(os.path.join(root, file), stream_folder).replace(os.sep, '/')
                    files_list.append(file_path)
                    for pattern, data_type in file_types.items():
                        if re.match(pattern, file, re.IGNORECASE):
                            if self.classify_to_folders.isChecked():
                                f.write(f"data_file '{data_type}' 'data/**/{file}'\n")
                            else:
                                f.write(f"data_file '{data_type}' '{file_path}'\n")
                            break

            if self.classify_to_folders.isChecked():
                f.write("files {\n")
                for file in files_list:
                    f.write(f"    'data/**/{file}',\n")
                f.write("}\n")

    def process_zip_files(self, zip_paths):
        temp_folder = 'temp_extracted'
        try:
            base_stream_folder = os.path.join(temp_folder, 'stream')
            if not os.path.exists(base_stream_folder):
                os.makedirs(base_stream_folder)

            for zip_path in zip_paths:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_folder)

                # 处理文件逻辑
                if self.classify_files.isChecked():
                    method = self.classification_method.currentText()
                    if method == self.get_text("By DLC Name", "按DLC名称"):
                        stream_folder = os.path.join(base_stream_folder, os.path.basename(zip_path).split('.')[0].split('_')[-1])
                    else:
                        stream_folder = base_stream_folder
                else:
                    stream_folder = base_stream_folder

                if not os.path.exists(stream_folder):
                    os.makedirs(stream_folder)

                # 处理车辆配件
                for root, dirs, files in os.walk(temp_folder):
                    for file in files:
                        if file.endswith('.rpf'):
                            src_path = os.path.join(root, file)
                            dst_path = os.path.join(stream_folder, 'mods', file)
                            shutil.move(src_path, dst_path)

                # 处理车辆模型和其他文件
                for root, dirs, files in os.walk(temp_folder):
                    for file in files:
                        if not file.endswith('.rpf'):
                            src_path = os.path.join(root, file)
                            dst_path = os.path.join(stream_folder, file)
                            if self.classify_to_folders.isChecked():
                                # 检查是否为音频文件或其他特定类型的数据文件
                                if 'audio' in root.lower() or 'dlc' in root.lower():
                                    folder_name = 'audio'
                                elif 'data' in root.lower():
                                    folder_name = 'data'
                                elif 'vehiclemods' in root.lower():
                                    folder_name = 'vehicles'
                                else:
                                    folder_name = ''
                                if folder_name:
                                    dst_path = os.path.join(stream_folder, folder_name, file)
                                shutil.move(src_path, dst_path)
                            else:
                                shutil.move(src_path, dst_path)

                if not self.save_original.isChecked():
                    os.remove(zip_path)

            # 创建FX资源清单文件
            self.create_fxmanifest(base_stream_folder, zip_name)
            
            # 保存转换后的ZIP文件
            converted_file_path = 'converted_mods.zip'
            with zipfile.ZipFile(converted_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(base_stream_folder):
                    for file in files:
                        zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), base_stream_folder))

            # 清理临时文件夹
            shutil.rmtree(temp_folder)
            
            QMessageBox.information(self, self.get_text("Success", "成功"), f"{self.get_text('Conversion completed successfully! File saved at:', '转换成功！文件已保存到：')} {converted_file_path}")
        except Exception as e:
            QMessageBox.critical(self, self.get_text("Error", "错误"), f"{self.get_text('Error during conversion:', '转换过程中出现错误：')} {str(e)}")

    def startConversion(self):
        dlc_paths = self.dlc_paths.text().split(',')
        dlc_paths = [path.strip() for path in dlc_paths if path.strip()]

        if not dlc_paths:
            QMessageBox.warning(self, self.get_text("Warning", "警告"), self.get_text("Please enter URLs or select DLC files to convert.", "请输入URL或选择DLC文件进行转换。"))
            return

        self.status_label.setText(self.get_text("Converting...", "转换中..."))

        downloaded_paths = []
        for path in dlc_paths:
            if path.startswith("http"):  # 下载链接
                save_path, _ = QFileDialog.getSaveFileName(self, self.get_text("Save Downloaded File", "保存下载的文件"), "", "ZIP Files (*.zip)")
                if save_path:
                    downloaded_path = self.downloadFile(path, save_path)
                    if downloaded_path:
                        downloaded_paths.append(downloaded_path)
            else:  # 直接处理本地文件
                downloaded_paths.append(path)

        if downloaded_paths:
            self.process_zip_files(downloaded_paths)

        self.status_label.setText(self.get_text("Ready", "就绪"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MultiFiveMModConverter()
    ex.show()
    sys.exit(app.exec_())