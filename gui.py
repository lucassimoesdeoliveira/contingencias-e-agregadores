# -*- coding: utf-8 -*-
"""

TODO: 
    ok - arrumar tab_conting nome dos arqvs
    clean up depois de concluido
    flag pra só recalcular tudo se mudar pwfs
    disabilitar mainwindow durante execução
    
    # tab_agreg
    ok - carregar pwfs se anarede não estiver checado
    ok - criar estrutura de pastas se não houver (só agreg)
    ok - usar o resource system para os icones
    
"""
import os
import re
import sys
import time
import subprocess
import epecontingencias as epe
import epeagregadores as epe_agreg
from PyQt5 import QtCore, QtGui, QtWidgets
from ui.main_window import Ui_Janela
from ui.ignora_barras_window import Ui_Janelinha

# Ajusta GUI para telas de alta resolução     
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling,True)
if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

# magia negra para mudar ícone na barra de tarefas    
try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin
    myappid = 'br.gov.epe.contingenciaagregadores.gui.1.0'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class Dialog(QtWidgets.QDialog, Ui_Janela):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        # dicts de checkboxes (p/ organizar os filtros)
        self.uf_cbs ={self.cb_AC:'AC', self.cb_AL:'AL', self.cb_AM:'AM',
                      self.cb_AP:'AP', self.cb_BA:'BA', self.cb_CE:'CE',
                      self.cb_DF:'DF', self.cb_ES:'ES', self.cb_GO:'GO',
                      self.cb_MA:'MA', self.cb_MG:'MG', self.cb_MS:'MS',
                      self.cb_MT:'MT', self.cb_PA:'PA', self.cb_PB:'PB',
                      self.cb_PE:'PE', self.cb_PI:'PI', self.cb_PR:'PR',
                      self.cb_RJ:'RJ', self.cb_RN:'RN', self.cb_RO:'RO',
                      self.cb_RR:'RR', self.cb_RS:'RS', self.cb_SC:'SC',
                      self.cb_SE:'SE', self.cb_SP:'SP', self.cb_TO:'TO'}
        self.vmon_cbs = {self.cb_l69m: [13,34], self.cb_69m : [69], 
                         self.cb_88m : [88]   , self.cb_115m: [115],
                         self.cb_138m: [138]  , self.cb_161m: [161],
                         self.cb_230m: [230]  , self.cb_345m: [345],
                         self.cb_440m: [440]  , self.cb_500m: [500],
                         self.cb_525m: [525]  , self.cb_765m: [765]}
        self.vconting_cbs = {self.cb_l69c: [13,34], self.cb_69c : [69],
                             self.cb_88c : [88]   , self.cb_115c: [115],
                             self.cb_138c: [138]  , self.cb_161c: [161],
                             self.cb_230c: [230]  , self.cb_345c: [345],
                             self.cb_440c: [440]  , self.cb_500c: [500],
                             self.cb_525c: [525]  , self.cb_765c: [765]}
        self.vcontrol_cbs = {self.cb_allDISTRm: [69,88,115,138,161],
                             self.cb_allRBm: [230,345,440,500,525,765],
                             self.cb_allDISTRc: [69,88,115,138,161],
                             self.cb_allRBc: [230,345,440,500,525,765]}
        
        # instancia janela auxiliar da lista-ignora
        ignora = [5190,5191,5192,5193,5194,5195,5196,5197,5200,
                  5201,5205,38863,38864,41973,42158,42159,42160,
                  4947,5206,4943,60189,4479,4480,60242,60241,
                  60211,60213,60214,]
        self.model_ignora = IgnoraModel(ignora)
        self.dialog_ignora = DialogIgnora(self.model_ignora)
        
        # instancia o gerenciador de threads
        self.threadpool = QtCore.QThreadPool()
        
        # definições de outras variáveis de instância 
        self.ufs = []
        self.vmons = {69,88,115,138,161,230,345,440,500,525,765}
        self.vcontings = {230,345,440,500,525,765}
        
        # modelo de dados para arquivos pwfs carregados
        self.model = PwfsModel()
        self.listView_arqv_carregados.setModel(self.model)

        # conexões signal-slots
        self.pushButton_saida.pressed.connect(self.executa_algoritmo)
        self.pushButton_carrega_arqvs.pressed.connect(self.seleciona_pwfs)
        self.pushButton_remover.pressed.connect(self.deleta_pwfs)
        self.pushButton_ignora.pressed.connect(self.invoca_dialog_ignora)
        for cb in self.uf_cbs:
            cb.stateChanged.connect(self.atualiza_filtros_ufs)
        for cb in self.vmon_cbs:
            cb.stateChanged.connect(self.atualiza_filtros_vmon)
        for cb in self.vconting_cbs:
            cb.stateChanged.connect(self.atualiza_filtros_vconting)
        for cb in self.vcontrol_cbs:
            cb.stateChanged.connect(self.atualiza_filtros_vcontrol)
            
        # #========== ABA AGREGADORES

        self.cb_anarede.setStyleSheet(':checked{background:rgba(255,0,0,.4)}')
        
        # flag de execução automática do Anarede
        self.anarede = True
        self.ana_path = r'C:\Cepel\Anarede\V110602\ANAREDE.exe'
        # self.ano_inic = 2024
        # self.ano_final = 2033        
        self.posicoes = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36]
        self.flag_posic_ok = True
        
        # modelo de dados para arquivos arqvs carregados
        self.model_agreg = AgregModel(self.anarede)
        self.listView_arqv_carregados_agreg.setModel(self.model_agreg) 
        
        # conexões signal-slots
        self.pushButton_saida_agreg.pressed.connect(
                                                self.executa_algoritmo_agreg)
        self.pushButton_carrega_arqvs_agreg.pressed.connect(
                                                        self.seleciona_arqvs)
        self.pushButton_remover_agreg.pressed.connect(self.deleta_arqvs)
        self.cb_anarede.stateChanged.connect(self.atualiza_anarede)
        # self.sb_anoinic.valueChanged.connect(self.atualiza_anos)
        # self.sb_anofinal.valueChanged.connect(self.atualiza_anos)
        self.le_posicoes.textChanged.connect(self.atualiza_anos)

    def executa_algoritmo(self):
        if not self.ufs:
            self.label_loading.setText('Selecione ao menos uma UF!')
            return
        if not self.model.pwfs:
            self.label_loading.setText('Selecione ao menos um arquivo .pwf!')
            return
        worker = Worker(self.model.pwfs, self.model_ignora.barras, self.ufs, 
                        self.vmons, self.vcontings)
        worker.signals.progresso.connect(self.atualiza_progresso)
        worker.signals.prog_label.connect(self.atualiza_prog_label)
        # Inicia execução do objeto worker q carrega o algoritmo principal
        self.threadpool.start(worker)
        
    def seleciona_pwfs(self):
        self.files, __ = QtWidgets.QFileDialog.getOpenFileNames(self,
                    "Selecione os arquivos .PWF dos casos a serem analisados",
                    "./pwfs/",
                    "Casos de flow (*.pwf)")
        # print(self.files)
        arqvs = [tuple(file.rsplit('/',1)) for file in self.files]  
        # print(arqvs)
        self.model.pwfs.extend(arqvs)
        self.model.layoutChanged.emit()
        # reseta barra de loading
        self.label_loading.setText('')
        self.progressBar.setValue(0)
        self.progressBar.setEnabled(False)
    
    def deleta_pwfs(self):
        indexes = self.listView_arqv_carregados.selectedIndexes()
        if indexes:
            index = sorted([i.row() for i in indexes], reverse=True)
            for ind in index:
                try:
                    del self.model.pwfs[ind]
                except IndexError:
                    pass
                self.model.layoutChanged.emit()
                self.listView_arqv_carregados.clearSelection()

    def invoca_dialog_ignora(self):
        self.dialog_ignora.show()
        # print(self.model_ignora.barras)
        # print(self.dialog_ignora.model_ignora.barras)
        
    def atualiza_progresso(self, progresso):
        self.progressBar.setEnabled(True)
        self.progressBar.setValue(progresso)
        if progresso == 100:
            self.progressBar.setEnabled(False)
            
    def atualiza_prog_label(self, texto):
        self.label_loading.setText(texto)
    
    def atualiza_filtros_ufs(self, state): 
        uf = self.uf_cbs[self.sender()]
        # print(uf)
        if state:
            self.ufs.append(uf)
        else:
            self.ufs.remove(uf)
        # print(self.ufs)
        
    def atualiza_filtros_vmon(self, state):
        vmon = self.vmon_cbs[self.sender()]
        # print('atualiza_filtros_vmon')
        # print(vmon)
        if state:
            self.vmons |= set(vmon)
        else:
            self.vmons -= set(vmon)
        # print(self.vmons)
    
    def atualiza_filtros_vconting(self, state):
        vconting = self.vconting_cbs[self.sender()]
        # print('atualiza_filtros_vmon')
        # print(vconting)
        if state:
            self.vcontings |= set(vconting)
        else:
            self.vcontings -= set(vconting) 
        # print(self.vcontings)
        
    def atualiza_filtros_vcontrol(self, state):
        if state:
            if self.sender() == self.cb_allDISTRm:
                self.cb_l69m.setChecked(False)
                self.cb_69m.setChecked(True)
                self.cb_88m.setChecked(True)
                self.cb_115m.setChecked(True)
                self.cb_138m.setChecked(True)
                self.cb_161m.setChecked(True)
            elif self.sender() == self.cb_allRBm:
                self.cb_230m.setChecked(True)
                self.cb_345m.setChecked(True)
                self.cb_440m.setChecked(True)
                self.cb_500m.setChecked(True)
                self.cb_525m.setChecked(True)
                self.cb_765m.setChecked(True)
            elif self.sender() == self.cb_allDISTRc:
                self.cb_l69c.setChecked(False)
                self.cb_69c.setChecked(True)
                self.cb_88c.setChecked(True)
                self.cb_115c.setChecked(True)
                self.cb_138c.setChecked(True)
                self.cb_161c.setChecked(True)
            elif self.sender() == self.cb_allRBc:
                self.cb_230c.setChecked(True)
                self.cb_345c.setChecked(True)
                self.cb_440c.setChecked(True)
                self.cb_500c.setChecked(True)
                self.cb_525c.setChecked(True)
                self.cb_765c.setChecked(True)
            # print('atualiza_filtros_vcontrol - on')
            # print(self.vcontings)
            # print(self.vmons)
        else:
            if self.sender() == self.cb_allDISTRm:
                self.cb_l69m.setChecked(False)
                self.cb_69m.setChecked(False)
                self.cb_88m.setChecked(False)
                self.cb_115m.setChecked(False)
                self.cb_138m.setChecked(False)
                self.cb_161m.setChecked(False)
            elif self.sender() == self.cb_allRBm:
                self.cb_230m.setChecked(False)
                self.cb_345m.setChecked(False)
                self.cb_440m.setChecked(False)
                self.cb_500m.setChecked(False)
                self.cb_525m.setChecked(False)
                self.cb_765m.setChecked(False)
            elif self.sender() == self.cb_allDISTRc:
                self.cb_l69c.setChecked(False)
                self.cb_69c.setChecked(False)
                self.cb_88c.setChecked(False)
                self.cb_115c.setChecked(False)
                self.cb_138c.setChecked(False)
                self.cb_161c.setChecked(False)
            elif self.sender() == self.cb_allRBc:
                self.cb_230c.setChecked(False)
                self.cb_345c.setChecked(False)
                self.cb_440c.setChecked(False)
                self.cb_500c.setChecked(False)
                self.cb_525c.setChecked(False)
                self.cb_765c.setChecked(False)
            # print('atualiza_filtros_vcontrol - off')
            # print(self.vcontings)
            # print(self.vmons)
    #=================== DRAG AND DROP AGREGADORES

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            links = []
            for url in event.mimeData().urls():
                # https://doc.qt.io/qt-5/qurl.html
                if url.isLocalFile():
                    links.append(str(url.toLocalFile()))
                else:
                    links.append(str(url.toString()))
            print(links)
            self.addItems(links)
        else:
            event.ignore()

    def addItems(self, links):
        # print(self.files)
        dropped_savs = [file for file in links if file[-4:].lower() == '.sav']

        if dropped_savs:
            self.seleciona_arqvs(dropped_savs)

    #=================== ABA AGREGADORES
    def seleciona_arqvs(self, files=None):
        if self.anarede:
            dir_ = "./savs/"
            filtro = "Arquivo histórico (*.sav)"
        else:
            dir_ = "./pwfs/"
            filtro = "Casos de flow (*.pwf)"

        if not files:
            self.files, __ = QtWidgets.QFileDialog.getOpenFileNames(self,
                    "Selecione os arquivos dos casos a serem analisados",
                    dir_, filtro)
        else:
            self.files = files
        # print(self.files)
        arqvs = [tuple(file.rsplit('/',1)) for file in self.files]  
        # print(arqvs)
        self.model_agreg.arqvs.extend(arqvs)
        self.model_agreg.layoutChanged.emit()
        
    def deleta_arqvs(self):
        indexes = self.listView_arqv_carregados_agreg.selectedIndexes()
        if indexes:
            index = sorted([i.row() for i in indexes], reverse=True)
            for ind in index:
                try:
                    del self.model_agreg.arqvs[ind]
                except IndexError:
                    pass
                self.model_agreg.layoutChanged.emit()
                self.listView_arqv_carregados_agreg.clearSelection()
    
    def atualiza_anarede(self, state): 
        icone_sav = QtGui.QIcon(':/icones/sav')
        icone_pwf = QtGui.QIcon(':/icones/pwf')
        if state:
            self.anarede = True
            # self.sb_anoinic.setEnabled(True)
            # self.sb_anofinal.setEnabled(True)
            self.le_posicoes.setEnabled(True)
            self.label_instrucao.setWordWrap(True)
            self.label_instrucao.setText('Ao fim da execução de cada etapa '
                                         'no Anarede, feche o programa para '
                                         'dar prosseguimento à rotina.')
            self.pushButton_carrega_arqvs_agreg.setText(
                                                    'Carregar arquivos .sav')
            self.pushButton_carrega_arqvs_agreg.setIcon(icone_sav)
            self.model_agreg = AgregModel(self.anarede)
            self.listView_arqv_carregados_agreg.setModel(self.model_agreg) 
        else:
            self.anarede = False
            # self.sb_anoinic.setEnabled(False)
            # self.sb_anofinal.setEnabled(False)
            self.le_posicoes.setEnabled(False)
            self.label_instrucao.setText('')
            self.pushButton_carrega_arqvs_agreg.setText(
                                                    'Carregar arquivos .pwf')
            self.pushButton_carrega_arqvs_agreg.setIcon(icone_pwf)
            self.model_agreg = AgregModel(self.anarede)
            self.listView_arqv_carregados_agreg.setModel(self.model_agreg) 

    def atualiza_anos(self, value):
        # if self.sender() == self.sb_anoinic:
        #     if value > self.ano_final: 
        #         self.sb_anoinic.setValue(self.ano_final)
        #         self.ano_inic = self.ano_final
        #     else:
        #         self.ano_inic = value
        # elif self.sender() == self.sb_anofinal:
        #     if value < self.ano_inic: 
        #         self.sb_anofinal.setValue(self.ano_inic)
        #         self.ano_final = self.ano_inic
        #     else:
        #         self.ano_final = value
        posic = value.replace(' ','').split(',')
        
        ## trata intervalos contínuos com hífen
        try:
            interv = []
            for idx, pos in enumerate(posic): 
                if pos.find('-')!=-1:
                    aux = posic.pop(idx).split('-')
                    aux = [int(i) for i in aux]
                    aux = list(range(aux[0],aux[1]+1))
                    interv.extend(aux)
            posic = [int(pos) for pos in posic]
            posic.extend(interv)
            posic = list(set(posic))
            posic.sort()
        except (ValueError, IndexError):
            self.flag_posic_ok = False
        
        if len(posic)!=0:
            if isinstance(posic[0], int):
                self.le_posicoes.setStyleSheet('color: black')
                self.flag_posic_ok = True
                self.posicoes = posic
            else:
                self.le_posicoes.setStyleSheet('color: red')
                self.flag_posic_ok = False
        else:
            self.le_posicoes.setStyleSheet('color: red')
            self.flag_posic_ok = False

        print(posic)
        print(self.flag_posic_ok)

    def executa_algoritmo_agreg(self):
        # teste de savs
        if not self.model_agreg.arqvs:
            self.label_agreg.setText(
                                'Selecione ao menos um arquivo .pwf/.sav!')
            self.label_agreg.setStyleSheet('color: red')
            return 
        # teste de posições
        if not self.flag_posic_ok:
            self.label_agreg.setText(
                            'Posições informadas em formato inconsistente!')
            self.label_agreg.setStyleSheet('color: red')
            return
                   
        if (self.anarede and not os.path.isfile(self.ana_path)):
            self.ana_path, __ = QtWidgets.QFileDialog.getOpenFileNames(
                        self,
                        "Indique/confirme o caminho do executável ANAREDE.exe",
                        self.ana_path,
                        "Arquivo executável (*.exe)")
            self.ana_path = self.ana_path[0]

        self.label_agreg.setText('')
        self.label_agreg.setStyleSheet('color: black')
        # anos = range(self.ano_inic-2000, self.ano_final+1-2000)
        anos  = self.posicoes
        files = ['/'.join(f) for f in self.model_agreg.arqvs]
        wdir = os.getcwd()
        regex = '[^\\/]+?(?=\.\w+$)'
        
        try:
            os.mkdir('./agregadores/')
        except OSError:
            pass
        
        if not self.anarede:                         
            nomes_pwfs = [re.search(regex,f).group(0) for f in files]
            
            epe_agreg.gera_pwf_dados_agregadores()
            epe_agreg.gera_pwf_agregadores(files, nomes_pwfs)

            self.label_agreg.setText('Arquivos salvos na pasta ./agregadores/')
        else:
            try:
                os.mkdir('./pwfs/')
            except OSError:
                pass
            
            nomes_savs = [re.search(regex,f).group(0) for f in files]
            savs = dict(zip(files, nomes_savs))

            epe_agreg.gera_pwf_dados_agregadores()
            export, pwfs = epe_agreg.gera_pwf_exporta_casos(savs, anos)
            
            nomes_pwfs = [re.search(regex,f).group(0) for f in pwfs]
            
            #self.label_agreg.setText('Gerando pwfs de cada posição do .sav...' 
            #                         ' (feche o Anarede assim que concluído)')
            self.label_agreg.setText('processando pwfs e aplicando dados de ' 
                                     'agregadores (feche o '
                                     'Anarede quando concluído)')
            self.label_agreg.repaint()

            subprocess.run([self.ana_path, wdir+export])
            
            self.label_agreg.setText('Computando dados de agregadores dos ' 
                                     'casos... (feche o Anarede quando '
                                     'concluído)')
            self.label_agreg.repaint()
            epe_agreg.gera_pwf_agregadores(pwfs, nomes_pwfs)
            
            salvar = epe_agreg.gera_pwf_salvar_agregadores(savs, anos)
            
            self.label_agreg.setText('Aplicando os dados de agregadores aos ' 
                                     'casos... (feche o Anarede quando '
                                     'concluído)')
            self.label_agreg.repaint()
            subprocess.run([self.ana_path, wdir+salvar])
            
            self.label_agreg.setText('Processo concluído!')
            

class DialogIgnora(QtWidgets.QDialog, Ui_Janelinha):
    def __init__(self, model_ignora, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        # uic.loadUi("./resources/dialog_ignora.ui", self)
        # icon = QtGui.QIcon('./resources/logo-epe.png')
        # self.setWindowIcon(icon)
        
        self.pushButton_incluir.pressed.connect(self.inclui_barra)
        self.pushButton_removerselec.pressed.connect(self.remove_barras)
        
        # modelo de dados da janela ignora passado da main_window
        self.model_ignora = model_ignora
        self.listView.setModel(self.model_ignora)
        
    def inclui_barra(self):
        nbarra = self.lineEdit_nbarra.text()
        try:
            if nbarra: 
                nbarra = int(nbarra.strip())
                self.model_ignora.barras.append(nbarra)              
                self.model_ignora.layoutChanged.emit()
                self.lineEdit_nbarra.setText("")
        except ValueError:
            self.lineEdit_nbarra.setText("")
        # print(self.model_ignora.barras)
  
    def remove_barras(self):
        indexes = self.listView.selectedIndexes()
        if indexes:
            index = sorted([i.row() for i in indexes], reverse=True)
            for ind in index:
                try:
                    del self.model_ignora.barras[ind]
                except IndexError:
                    pass
                self.model_ignora.layoutChanged.emit()
                self.listView.clearSelection()
        # print(self.model_ignora.barras)


class WorkerSignals(QtCore.QObject):
    """
    Define os signals de um objeto Worker executando numa thread.
    """
    progresso = QtCore.pyqtSignal(int)
    prog_label = QtCore.pyqtSignal(str)


class Worker(QtCore.QRunnable):
    """
    Define o objeto Worker que executa numa thread e devolve signal do
    progresso.
    """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self.model_arqv, self.model_ignora, self.ufs, self.vmons, \
                                                      self.vcontings = args
        self.model_arqv = ['/'.join(f) for f in self.model_arqv]
        
    @QtCore.pyqtSlot()
    def run(self):
        self.signals.progresso.emit(1)
        self.signals.prog_label.emit('carregando dados de DBAR...')
        self.dbar = epe.lista_obras('DBAR', self.model_arqv, self.model_ignora)
        
        self.signals.progresso.emit(28)
        self.signals.prog_label.emit('carregando dados de DLIN...')
        self.dlin = epe.lista_obras('DLIN', self.model_arqv, self.model_ignora)
        
        self.signals.progresso.emit(56)
        self.signals.prog_label.emit('identificando barras fictícias...')
        time.sleep(1.0)
        self.dbar = epe.id_barrafict(self.dbar)
        
        self.signals.progresso.emit(57)
        self.signals.prog_label.emit('processando informações de rede...')
        self.dbar, self.dlin, self.dtrf = epe.processa_dados_rede(self.dbar,
                                                                  self.dlin)
        self.signals.progresso.emit(97)
        self.signals.prog_label.emit('filtrando dados resultantes...')
        time.sleep(1.5)
        self.dbar, self.dlin, self.dtrf = epe.filtragem(self.dbar, self.dlin,
                                                        self.dtrf, self.ufs, 
                                                        self.vmons,
                                                        self.vcontings)
        self.signals.progresso.emit(98)
        self.signals.prog_label.emit('escrevendo arquivo monitora.dat...')
        self.dLT, self.dTR, self.circs = epe.define_monitora(self.dbar,
                                                             self.dlin,
                                                             self.dtrf)
        
        self.signals.progresso.emit(99)
        self.signals.prog_label.emit('escrevendo tabela de contingências...')
        epe.escreve_tabela_conting(self.dLT, self.dTR, self.circs, 
                                   self.vcontings, self.model_arqv)
        time.sleep(1.0)
        self.signals.progresso.emit(100)
        self.signals.prog_label.emit('Processo concluído!')
        
        
class PwfsModel(QtCore.QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.pwfs = []
        self.icone_pwf = QtGui.QIcon(':/icones/pwf')

    def rowCount(self, index):
        return len(self.pwfs)
         
    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            path, pwf = self.pwfs[index.row()]
            # print(pwf)
            return pwf
        if role == QtCore.Qt.DecorationRole:
            return self.icone_pwf
        

class IgnoraModel(QtCore.QAbstractListModel):
    def __init__(self, ignora=None):
        super().__init__()
        self.barras = ignora or []
        self.icone_bus = QtGui.QIcon(':/icones/bus')
        
    def rowCount(self, index):
        return len(self.barras)
         
    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            barra = self.barras[index.row()]
            return barra
        if role == QtCore.Qt.DecorationRole:
            return self.icone_bus


#================= ABA AGREGADORES
class AgregModel(QtCore.QAbstractListModel):
    def __init__(self, anarede):
        super().__init__()
        self.arqvs = []
        self.icone_sav = QtGui.QIcon(':/icones/sav')
        self.icone_pwf = QtGui.QIcon(':/icones/pwf')
        self.anarede = anarede

    def rowCount(self, index):
        return len(self.arqvs)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            path, arqv = self.arqvs[index.row()]
            return arqv
        if role == QtCore.Qt.DecorationRole:
            if self.anarede:
                return self.icone_sav
            else:
                return self.icone_pwf


if __name__ == '__main__':
    def run_app():
        app = QtWidgets.QApplication(sys.argv)
        window = Dialog()
        window.show()
        sys.exit(app.exec_())
    run_app()
