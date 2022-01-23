# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 09:23:19 2019
pip install StringDist
@author: samir.ferreira
"""
import io
import pandas as pd
# import stringdist as sd
import numpy as np


def carrega_pwf(path):
    """
    Lê um caso .PWF e cria um dicionário contendo com cada Código
    de Execução do Anarede com uma chave para um DataFrame

    Args:
        path: Caminho para o arquivo .PWF

    Returns:
        a função retorna um dicionário, no qual cada key é um código
        de execução Anarede (ex: 'DBAR'), e contém os respectivos dados
        em formato de um pandas DataFrame

    Raises:
    
    OBS: 
        Não lê TITU e DAGR apropriadamente por não terminar em 99999 
        DAGR não tratado (é 2+ linhas semelhante a DBSH)
    
    """
    # DEFINIÇÃO LARGURAS ======================================================
    DBARw = [(0, 5), (5, 6), (6, 7), (7, 8), (8, 10), (10, 22), (22, 24),
             (24, 28), (28, 32), (32, 37), (37, 42), (42, 47), (47, 52),
             (52, 58), (58, 63), (63, 68), (68, 73), (73, 76), (76, 80),
             (80, 81), (81, 84), (84, 87), (87, 90), (90, 93), (93, 96),
             (96, 99), (99, 102), (102, 105), (105, 108), (108, 111)]
    DLINw = [(0, 5), (5, 6), (7, 8), (9, 10), (10, 15), (15, 17), (17, 18),
             (18, 19), (20, 26), (26, 32), (32, 38), (38, 43), (43, 48),
             (48, 53), (53, 58), (58, 64), (64, 68), (68, 72), (72, 74),
             (74, 78), (78, 81), (81, 84), (84, 87), (87, 90), (90, 93),
             (93, 96), (96, 99), (99, 102), (102, 105), (105, 108)]
    DSHLw = [(0, 5), (6, 7), (9, 14), (14, 16), (17, 23), (23, 29), (30, 32),
             (33, 35)]
    DBSHw = [(0, 5), (6, 7), (8, 13), (14, 16), (17, 18), (19, 23), (24, 28),
             (29, 34), (35, 41), (42, 43), (44, 45), (46, 51), (52, 54),
             (55, 57), (57, 59), (59, 63), (63, 67), (67, 74)]
    TITUw = [(0, 79),]
    DOPCw = [(0, 4), (5, 6), (7, 11), (12, 13), (14, 18), (19, 20), (21, 25),
            (26, 27), (28, 32), (33, 34), (35, 39), (40, 41), (42, 46),
            (47, 48), (49, 53), (54, 55), (56, 60), (61, 62), (63, 67),
            (68, 69)]
    DCTEw = [(0, 4), (5, 11), (12, 16), (17, 23), (24, 28), (29, 35), (36, 40),
            (41, 47), (48, 52), (53, 59), (60, 64), (65, 71)]
    DCSCw = [(0, 5), (6, 7), (9, 14), (14, 16), (16, 17), (17, 18), (18, 19),
            (25, 31), (31, 37), (37, 43), (43, 44), (45, 51), (52, 57),
            (57, 60), (60, 64), (64, 68), (68, 72), (72, 75), (75, 78),
            (78, 81), (81, 84), (84, 87), (87, 90), (90, 93), (93, 96),
            (96, 99), (99, 102)]
    DGERw = [(0, 5), (6, 7), (8, 14), (15, 21), (22, 27), (28, 33), (34, 39),
            (40, 44), (45, 49), (50, 54), (55, 60), (61, 66), (67, 72)]
    DCERw = [(0, 5), (6, 7), (8, 10), (11, 13), (14, 19), (20, 26), (27, 32),
            (32, 37), (37, 42), (43, 44), (45, 46)]
    DCTRw = [(0, 5), (6, 7), (8, 13), (14, 16), (17, 21), (22, 26), (27, 28),
            (29, 30), (31, 37), (38, 44), (45, 46), (47, 53), (54, 59),
            (60, 62)]
    DGLTw = [(0, 2), (3, 8), (9, 14), (15, 20), (21, 26), ]
    DAREw = [(0, 3), (7, 13), (18, 54), (55, 61), (62, 68), ]
    DTPFw = [(0, 5), (6, 11), (12, 14), (15, 20), (21, 26), (27, 29), (30, 35),
            (36, 41), (42, 44), (45, 50), (51, 56), (57, 59), (60, 65),
            (66, 71), (72, 74), (75, 76)]
    DELOw = [(0, 4), (5, 6), (7, 12), (13, 18), (19, 39), (40, 41), (42, 43)]
    DCBAw = [(0, 4), (5, 6), (7, 8), (8, 9), (9, 21), (21, 23), (23, 28),
            (66, 71), (71, 75)]
    DCLIw = [(0, 4), (5, 6), (8, 12), (12, 14), (15, 16), (17, 23), (23, 29),
            (60, 64)]
    DCNVw = [(0, 4), (5, 6), (7, 12), (13, 17), (18, 22), (23, 24), (25, 26),
            (27, 32), (33, 38), (39, 44), (45, 50), (51, 56), (57, 62),
            (63, 68), (69, 71)]
    DCCVw = [(0, 4), (5, 6), (7, 8), (8, 9), (9, 10), (11, 16), (17, 22),
            (23, 28), (29, 34), (35, 40), (41, 46), (47, 52), (53, 58),
            (59, 61), (62, 66), (67, 72), (73, 78)]
    DGBTw = [(0, 2), (3, 8)]
    DCMTw = [(0, 81),]
        
    # DEFINIÇÃO NOMES COLUNAS =================================================
    DBARc = ('Num', 'O', 'E', 'T', 'Gb', 'Nome', 'Gl', 'V', 'A', 'Pg', 'Qg',
             'Qn', 'Qm', 'Bc', 'Pl', 'Ql', 'Sh', 'Are', 'Vf', 'M', 'A1', 'A2',
             'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10')
    DLINc = ('De', 'Dde', 'O', 'Dpara', 'Para', 'Nc', 'E', 'P', 'R', 'X',
             'Mvar', 'Tap', 'Tmn', 'Tmx', 'Phs', 'Bc', 'Cn', 'Ce', 'Ns', 'Cq',
             'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10')
    DSHLc = ('De', 'O', 'Para', 'Nc', 'Shde', 'Shpara', 'Ed', 'Ep', )    
    DBSHc = ('De', 'O', 'Para', 'Nc', 'C', 'Vmn', 'Vmx', 'Bctrl', 'Qini', 'T',
             'A', 'Extr', 'G', 'Og', 'E', 'U', 'Uop', 'Sht')    
    TITUc = ('Titulo', )
    DOPCc = ('Op1', 'E1', 'Op2', 'E2', 'Op3', 'E3', 'Op4', 'E4', 'Op5', 'E5',
            'Op6', 'E6', 'Op7', 'E7', 'Op8', 'E8', 'Op9', 'E9', 'Op10', 'E10')
    DCTEc = ('Mn1', 'Val1', 'Mn2', 'Val2', 'Mn3', 'Val3', 'Mn4', 'Val4', 'Mn5',
            'Val5', 'Mn6', 'Val6')
    DCSCc = ('De', 'O', 'Para', 'Nc', 'E', 'P', 'B', 'Xmin', 'Xmax', 'Xv', 'C',
            'Vsp', 'Ext', 'Nst', 'Cn', 'Ce', 'Cq', 'A1', 'A2', 'A3', 'A4',
            'A5', 'A6', 'A7', 'A8', 'A9', 'A10')
    DGERc = ('Num', 'O', 'Pmn', 'Pmx', 'Fp', 'FpR', 'FPn', 'Fa', 'Fr', 'Ag',
            'Xq', 'Sno', 'Est')
    DCERc = ('Num', 'O', 'Gr', 'Un', 'Kb', 'Incl', 'Qg', 'Qn', 'Qm', 'C', 'E')
    DCTRc = ('De', 'O', 'Para', 'Nc', 'Vmin', 'Vmax', 'Tc', 'M', 'Fmin',
            'Fmax', 'Mc', 'Vsp', 'Ext', 'Ns')
    DGLTc = ('Grupo', 'Vmin', 'Vmax', 'Vmne', 'Vmxe')
    DAREc = ('Num', 'Xchg', 'Nome', 'Xmin', 'Xmax')
    DTPFc = ('De1', 'Para1', 'Nc1', 'De2', 'Para2', 'Nc2', 'De3', 'Para3',
            'Nc3', 'De4', 'Para4', 'Nc4', 'De5', 'Para5', 'Nc5', 'O')
    DELOc = ('Num', 'O', 'V', 'P', 'Nome', 'M', 'E')
    DCBAc = ('Num', 'O', 'T', 'P', 'Nome', 'Gl', 'Vd', 'Rs', 'Elo')
    DCLIc = ('De', 'O', 'Para', 'Nc', 'P', 'R', 'L', 'Cn')
    DCNVc = ('Num', 'O', 'Ca', 'Cc', 'El', 'T', 'P', 'Ino', 'Xc', 'Vfs', 'Snt',
            'Rra', 'Lra', 'Ccc', 'Fr')
    DCCVc = ('Num', 'O', 'F', 'M', 'C', 'Vsp', 'Marg', 'Imax', 'Dsp', 'Dtn',
            'Dtm', 'Tmn', 'Tmx', 'S', 'Vmn', 'Tmh', 'Ttr')
    DGBTc = ('G', 'kV')
    DCMTc = ('Comentário', )

    # DEFINIÇÃO DICIONARIOS ===================================================
    pwf_dict = {'DBAR':[], 'DLIN':[], 'DSHL':[], 'DBSH':[], 'TITU':[], 
                'DOPC':[], 'DCTE':[], 'DCSC':[], 'DGER':[], 'DCAR':[], 
                'DCER':[], 'DCTR':[], 'DGLT':[], 'DARE':[], 'DTPF':[], 
                'DELO':[], 'DCBA':[], 'DCLI':[], 'DCNV':[], 'DCCV':[], 
                'DGBT':[], 'DCMT':[],}
    WIDTH = {'DBAR':DBARw, 'DLIN':DLINw, 'DSHL':DSHLw, 'DBSH':DBSHw, 
             'TITU':TITUw, 'DOPC':DOPCw, 'DCTE':DCTEw, 'DCSC':DCSCw, 
             'DGER':DGERw, 'DCER':DCERw, 'DCTR':DCTRw, 'DGLT':DGLTw, 
             'DARE':DAREw, 'DTPF':DTPFw, 'DELO':DELOw, 'DCBA':DCBAw, 
             'DCLI':DCLIw, 'DCNV':DCNVw, 'DCCV':DCCVw, 'DGBT':DGBTw,
             'DCMT':DCMTw,}
    COL_NAMES = {'DBAR':DBARc, 'DLIN':DLINc, 'DSHL':DSHLc, 'DBSH':DBSHc,
                 'TITU':TITUc, 'DOPC':DOPCc, 'DCTE':DCTEc, 'DCSC':DCSCc,
                 'DGER':DGERc, 'DCER':DCERc, 'DCTR':DCTRc, 'DGLT':DGLTc, 
                 'DARE':DAREc, 'DTPF':DTPFc, 'DELO':DELOc, 'DCBA':DCBAc, 
                 'DCLI':DCLIc, 'DCNV':DCNVc, 'DCCV':DCCVc, 'DGBT':DGBTc, 
                 'DCMT':DCMTc,}
    COD_EXEC = ('DBAR', 'DLIN', 'DSHL', 'DBSH', 'TITU', 'DOPC', 'DCTE', 'DGER',
                'DCSC', 'DCAR', 'DCER', 'DCTR', 'DGLT', 'DARE', 'DTPF', 'DELO', 
                'DCBA', 'DCLI', 'DCNV', 'DCCV', 'DGBT', 'DCMT',)

    exec_atual = []
    process_flag = True
    nfr_flag = True
        
    with open(path, 'r') as file:
        for line in file:
            line = line.strip('\n')
            if line[:4] in COD_EXEC:
                process_flag = True
                exec_atual = line[:4]
                buffer = io.StringIO()
                continue
            
            if (line != '99999') and (line != 'FIM') and \
               (exec_atual in COD_EXEC) and (line[0] != '(') and process_flag:   # process_flag serve para barrar leitura se um buffer valido não estiver aberto
                   
                if (exec_atual == 'DBSH'):                                      # trata o caso especial do DBSH 2ou+ linhas
                    if line[0:4] == 'FBAN':
                        nfr_flag = True
                        continue
                    else:
                        if nfr_flag: 
                            nfr_header = line
                            nfr_flag = False
                            continue
                        if not nfr_flag:
                            try:
                                buffer.write(nfr_header + line + '\n')
                            except:
                                print('falha durante a escrita da linha no '
                                      f'buffer do {exec_atual}')
                                print(f'linha = {line}')
                                break
                else:                                                           # trata todos os outros CODEXEC de uma linha    
                    try:
                        buffer.write(line + '\n')
                    except:
                        print('falha durante a escrita da linha no buffer'
                              f' do {exec_atual}')
                        print(f'linha = {line}')
                        break
                
            if (line == '99999') or (line[:4] in COD_EXEC):
                process_flag = False
                try:
                    buffer.seek(0)
                    pwf_dict[exec_atual] = pd.read_fwf(buffer,
                                                colspecs=WIDTH[exec_atual],
                                                names=COL_NAMES[exec_atual])
                    # pwf_dict[exec_atual].fillna('',inplace=True)
                    buffer.close()
                except:
                    pass
    file.close()

    return pwf_dict


def escreve_monitora(mon_dict, mon_path = 'output.DAT'):
    """
    Escreve um arquivo monitora.DAT com base em um dicionário de dataframes com 
    informações de cada cód. de execução do "monitora"

    Args:
        mon_dict: dict de dataframes de cada cód. de execução do "monitora".
        monPath: Nome para o arquivo .DAT resultante.
        
    Returns:

    """
    
    # DEFINIÇÃO LARGURAS ======================================================   
    DBTBw = [(0, 5), (6, 11), (12, 17), (80, 140)]
    DFTBw = [(0, 5), (6, 11), (12, 14), (15, 16), (17, 29), (29, 41), (42, 43),
             (44, 48), (49, 53), (54, 57), (59, 63), (64, 68), (69, 73),
             (74, 78), (80, 140)]
      
    
    WIDTH = {
        'DBTB': [i[1]-i[0] for i in DBTBw],
        'DFTB': [i[1]-i[0] for i in DFTBw],
    }
    
    
    EMPTY = {
        'DBTB': [' ',' ','',''],
        'DFTB': [' ',' ',' ',' ','',' ',' ',' ',' ',' ',' ',' ',' ','',''],
    }
        
    COD_EXEC_exception = ()   # códigos que não terminam em 99999 (valeu cepel!)
    
    for cod_exec in mon_dict:
        aux = mon_dict[cod_exec].values.tolist()
        
        ## converte list de list de varios types em list de list de str
        mon_list = []
        for ind, line in enumerate(aux):
            result = map(str, aux[ind][:]) 
            mon_list.append(list(result))
        
        ## aplica o fixedwidth para cada campo
        fwt = []
        for line in mon_list:
            string = ""
            for j in range(0,len(line)):
                line[j] ='{dat:>{wid}}'.format(dat=line[j], wid=WIDTH[cod_exec][j])
                try:
                    string = string + line[j][:WIDTH[cod_exec][j]] + EMPTY[cod_exec][j]
                except:
                    string = string + line[j] + EMPTY[cod_exec][j]
            fwt.append(string)
        
        ## escreve o arquivo    
        with open(mon_path, 'a+') as file:
            file.write(cod_exec + '\n')
            for line in fwt:
                file.write(''.join(line) + '\n')
            if (cod_exec not in COD_EXEC_exception):
                file.write('99999\n')
    with open(mon_path, 'a+') as file:
        file.write('FIM\n')      

def carrega_ana(path_to_file):
    """
    Lê um caso .PWF e cria um dicionário contendo com cada Código
    de Execução do Anarede com uma chave para um DataFrame

    Args:
        path_to_file: Caminho para o arquivo .PWF

    Returns:
        a função retorna um dicionário, no qual cada key é um código
        de execução Anarede (ex: 'DBAR'), e contém os respectivos dados
        em formato de um pandas DataFrame

    Raises:

    """
    # DEFINIÇÃO LARGURAS ======================================================

    TIPOw = [(0,3)]
    
    TITUw = [(0,78)]
    
    DBARw = [(0, 5), (5, 6), (6, 7), (7, 8), (9, 21), (22, 26), (26, 30),
             (31, 35), (36, 42), (52, 54), (54, 56), (56, 60), (60, 62),
             (62, 64), (64, 68), (69, 72), (72, 75), (76, 77)]

    DCIRw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (16, 17), (17, 23), 
             (23, 29), (29, 35), (35, 41), (41, 47), (47, 52), (52, 57), 
             (57, 62), (62, 67), (67, 69), (69, 72), (72, 75), (75, 76), 
             (76, 80), (80, 82), (82, 88), (88, 94), (94, 96), (96, 102),
             (102, 108), (108, 111), (115, 118), (118, 121), (122, 128),
             (128, 131), (131, 137), (137, 140), (160, 162), (162, 164),
             (164, 168), (168, 170), (170, 172), (172, 176), (177, 182),
             (196, 198), (199, 219),
             (220, 221), (221, 222), (222, 223), (223, 224), (224, 225),   # campos de flags de ponto decimal
             (225, 226), (226, 227), (227, 228), (228, 229), (229, 230),
             (230, 231)]

    DSHLw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (16, 17), (17, 19), 
             (20, 26), (27, 28), (28, 34), (34, 40), (40, 41), (41, 47), 
             (48, 51), (51, 54), (69, 72), (72, 75), (109, 111), (112, 132)]

    DMUTw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (16, 21), (23, 28), 
             (30, 32), (32, 38), (38, 44), (45, 51), (51, 57), (57, 63), 
             (63, 69), (69, 72), (72, 75),
             (76, 77), (77, 78)]                                            # campos de flags de ponto decimal
    
    DMOVw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (17, 21), (22, 30), 
             (31, 39), (40, 48), (49, 57), (58, 66), (73, 74), (109, 111), 
             (199, 219)]
    
    DEOLw = [(0, 5), (5, 6), (6, 7), (14, 16), (17, 23), (23, 29), (29, 35), 
             (35, 41), (41, 47), (48, 51), (51, 54), (55, 61), (62, 68), 
             (69, 72), (73, 75), (76, 82), (82, 85), (86, 91), (92, 94), 
             (94, 96), (96, 100), (100, 102), (102, 104), (104, 108), (113, 132)]
    
    DAREw = [(0, 3), (5, 6), (18, 54)]
    
#    CMNTw = [(0,80)]
        
    # DEFINIÇÃO NOMES COLUNAS =================================================

    TIPOc = ('Tipo',)
    
    TITUc = ('Título',)
    
    DBARc = ('NB', 'Chng', 'E', 'MP', 'BN', 'VPRE', 'ANG', 'VBAS', 'DISJUN', 
             'DDi', 'MMi', 'AAAAi', 'DDf', 'MMf', 'AAAAf', 'IA', 'SA', 'F')

    DCIRc = ('BF', 'Chng', 'E', 'BT', 'Nc', 'TipC', 'R1', 'X1', 'R0', 'X0', 
             'CN', 'S1', 'S0', 'Tap', 'TB', 'TC', 'IA', 'DEF', 'IE', 'km', 'CD', 
             'RnDe', 'XnDe', 'CP', 'RnPa', 'XnPa', 'SA', 'Nun', 'Nop', 'DJ_BF',
             'CicF', 'DJ_BT', 'CicT', 'DDi', 'MMi', 'AAAAi', 'DDf', 'MMf',
             'AAAAf', 'MVA', 'TD', 'Nome',
             'fR1','fX1','fR0','fX0','fS1','fS0','fTap','fRnD','fXnD','fRnP',
             'fXnP')

    DSHLc = ('BF', 'Chng', 'E', 'BT', 'Nc', 'T', 'NG', 'Qpos', 'L', 'Rn', 'Xn',
             'Et', 'NomeEq', 'Nun', 'Nop', 'IA', 'SA', 'TD', 'Nome')      
    
    DMUTc = ('BF1', 'Chng', 'E', 'BT1', 'Nc1', 'BF2', 'BT2', 'Nc2', 'Rm', 'Xm',
             '%I1', '%F1', '%I2', '%F2', 'IA', 'SA',
             'fRm','fXm')  
    
    DMOVc = ('BF', 'Chng', 'E', 'BT', 'Nc', 'VBAS', 'IPR', 'IMAX', 'EMAX',
             'PMAX', 'VPR', 'D', 'TD', 'Nome')  
        
    DEOLc = ('NB', 'Chng', 'E', 'NG', 'Pinic', 'Imax', 'Vmin', 'FP_CC', 
             'Nome EOL', 'NUN', 'NOP', 'FP_pre', 'Vmax', 'IA', 'SA', 'Disjun',
             'Cic', 'MVA', 'DDi', 'MMi', 'AAAAi', 'DDf', 'MMf', 'AAAAf', 'Nome') 
    
    DAREc = ('Num', 'Chng', 'Nome') 
    
#    CMNTc = ('Comentário',)
    
    # DEFINIÇÃO DICIONARIOS ===================================================

    anaDict = {
        'TIPO': [],
        'TITU': [],
        'DBAR': [],
        'DCIR': [],
        'DSHL': [],
        'DMUT': [],
        'DMOV': [],
        'DEOL': [],
        'DARE': [],
#        'CMNT': [],
    }

    WIDTH = {
        'TIPO': TIPOw,
        'TITU': TITUw,
        'DBAR': DBARw,
        'DCIR': DCIRw,
        'DSHL': DSHLw,
        'DMUT': DMUTw,
        'DMOV': DMOVw,
        'DEOL': DEOLw,
        'DARE': DAREw,
#        'CMNT': CMNTw,
    }

    COL_NAMES = {
        'TIPO': TIPOc,
        'TITU': TITUc,
        'DBAR': DBARc,
        'DCIR': DCIRc,
        'DSHL': DSHLc,
        'DMUT': DMUTc,
        'DMOV': DMOVc,
        'DEOL': DEOLc,
        'DARE': DAREc,
#        'CMNT': CMNTc,
    }

    COD_EXEC = (
        'TIPO',
        'TITU',
        'DBAR',
        'DCIR',
        'DSHL',
        'DMUT',
        'DMOV',
        'DEOL',
        'DARE',
#        'CMNT',
    )
    
    COD_EXEC_exception = ('TIPO', 'TITU', 'CMNT')   # códigos que não terminam em 99999 (valeu cepel!)       
    DCIR_decimal = [(17, 23), (23, 29), (29, 35), (35, 41), (47, 52), (52, 57),   # códigos com ponto decimal implícito (valeu cepel!)
                    (57, 62), (82, 88), (88, 94), (96, 102), (102, 108)]
    DMUT_decimal = [(32, 38), (38, 44)]

    
    exec_atual = False
    process_flag = True

    with open(path_to_file, 'r') as file:
        for line in file:
            line = line.strip('\n')
            if line[:4] in COD_EXEC:
                process_flag = True
                exec_atual = line[:4]
                buffer = io.StringIO()
                continue
            
            if (line != '99999') and (line != 'FIM') and \
               (exec_atual in COD_EXEC) and (line[0] != '(') and process_flag:   # process_flag serve para barrar leitura se um buffer valido não estiver aberto
                
                #### trata ponto decimal implícito gerando flags para correção no dataframe!
                if (exec_atual == 'DCIR'):
                    line += ' '*(220-len(line))     # completa comprimento da régua para preencher flag no lugar correto
                    for interval in DCIR_decimal:
                        if (line.count('.',interval[0],interval[1]) > 0) or \
                            not (line[interval[0]:interval[1]].strip()):        # se tiver ponto ou estiver vazio faz nada 
                            line += '0'
                        else:
                            line += '1'
                if (exec_atual == 'DMUT'):
                    line += ' '*(79-len(line))     
                    for interval in DMUT_decimal:
                        if (line.count('.',interval[0],interval[1]) > 0) or \
                            not (line[interval[0]:interval[1]].strip()):
                            line += '0'
                        else:
                            line += '1'   
                ####-----------------------------------------------------------
                
                try:
                    buffer.write(line + '\n')
                except:
                    print(f'falha durante a escrita da linha no buffer do {exec_atual}')
                    print(f'linha = {line}')
                    break
                
            if (line == '99999') or (exec_atual in COD_EXEC_exception):
                process_flag = False
                try:
                    buffer.seek(0)
                    anaDict[exec_atual] = pd.read_fwf(buffer,
                                                      colspecs=WIDTH[exec_atual],
                                                      names=COL_NAMES[exec_atual])
                    anaDict[exec_atual].fillna("",inplace=True)                   
                    buffer.close()
                except:
                    pass
#            else
            
    file.close()
    
    #### trata ponto decimal implícito (/100) onde tem flag setado e deleta flags
    anaDict['DCIR'].loc[anaDict['DCIR']['fR1'] == 1, ['R1']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fX1'] == 1, ['X1']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fR0'] == 1, ['R0']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fX0'] == 1, ['X0']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fS1'] == 1, ['S1']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fS0'] == 1, ['S0']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fTap'] == 1, ['Tap']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fRnD'] == 1, ['RnDe']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fXnD'] == 1, ['XnDe']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fRnP'] == 1, ['RnPa']] *= .01
    anaDict['DCIR'].loc[anaDict['DCIR']['fXnP'] == 1, ['XnPa']] *= .01
    anaDict['DCIR'].drop(columns=['fR1','fX1','fR0','fX0','fS1','fS0','fTap',
                                   'fRnD','fXnD','fRnP','fXnP'], inplace=True)
    anaDict['DMUT'].loc[anaDict['DMUT']['fRm'] == 1, ['Rm']] *= .01
    anaDict['DMUT'].loc[anaDict['DMUT']['fXm'] == 1, ['Xm']] *= .01
    anaDict['DMUT'].drop(columns=['fRm','fXm'], inplace=True)               
    ##-------------------------------------------------------------------------
    
    return anaDict


def escreve_ana(anaDict, anaPath = 'output.ANA'):
    """
    Escreve um arquivo .ANA com base em um dicionário de dataframes com 
    informações de cada cód. de execução do ANAFAS

    Args:
        anaDict: dict de dataframes de cada cód. de execução do ANAFAS.
        anaPath: Nome para o arquivo .ANA resultante.
        
    Returns:

    """
    
    # DEFINIÇÃO LARGURAS ======================================================
    TIPOw = [(0,3)]
    
    TITUw = [(0,78)]
    
    DBARw = [(0, 5), (5, 6), (6, 7), (7, 8), (9, 21), (22, 26), (26, 30),
             (31, 35), (36, 42), (52, 54), (54, 56), (56, 60), (60, 62),
             (62, 64), (64, 68), (69, 72), (72, 75), (76, 77)]
    
    DCIRw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (16, 17), (17, 23), 
             (23, 29), (29, 35), (35, 41), (41, 47), (47, 52), (52, 57), 
             (57, 62), (62, 67), (67, 69), (69, 72), (72, 75), (75, 76), 
             (76, 80), (80, 82), (82, 88), (88, 94), (94, 96), (96, 102),
             (102, 108), (108, 111), (115, 118), (118, 121), (122, 128),
             (128, 131), (131, 137), (137, 140), (160, 162), (162, 164),
             (164, 168), (168, 170), (170, 172), (172, 176), (177, 182),
             (196, 198), (199, 219)]
    
    DSHLw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (16, 17), (17, 19), 
             (20, 26), (27, 28), (28, 34), (34, 40), (40, 41), (41, 47), 
             (48, 51), (51, 54), (69, 72), (72, 75), (109, 111), (112, 132)]
    
    DMUTw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (16, 21), (23, 28), 
             (30, 32), (32, 38), (38, 44), (45, 51), (51, 57), (57, 63), 
             (63, 69), (69, 72), (72, 75)]
    
    DMOVw = [(0, 5), (5, 6), (6, 7), (7, 12), (14, 16), (17, 21), (22, 30), 
             (31, 39), (40, 48), (49, 57), (58, 66), (73, 74), (109, 111), 
             (199, 219)]
    
    DEOLw = [(0, 5), (5, 6), (6, 7), (14, 16), (17, 23), (23, 29), (29, 35), 
             (35, 41), (41, 47), (48, 51), (51, 54), (55, 61), (62, 68), 
             (69, 72), (73, 75), (76, 82), (82, 85), (86, 91), (92, 94), 
             (94, 96), (96, 100), (100, 102), (102, 104), (104, 108), (113, 132)]
    
    DAREw = [(0, 3), (5, 6), (18, 54)]
    
#    CMNTw = [(0,80)]
        
    
    WIDTH = {
        'TIPO': [i[1]-i[0] for i in TIPOw],
        'TITU': [i[1]-i[0] for i in TITUw],
        'DBAR': [i[1]-i[0] for i in DBARw],
        'DCIR': [i[1]-i[0] for i in DCIRw],
        'DSHL': [i[1]-i[0] for i in DSHLw],
        'DMUT': [i[1]-i[0] for i in DMUTw],
        'DMOV': [i[1]-i[0] for i in DMOVw],
        'DEOL': [i[1]-i[0] for i in DEOLw],
        'DARE': [i[1]-i[0] for i in DAREw],
#        'CMNT': [i[1]-i[0] for i in CMNTw],
    }
    
    
    EMPTY = {
        'TIPO': [''],
        'TITU': [''],
        'DBAR': ['','','',' ',' ','',' ',' ','          ','','','','','',' ','',' ',''],
        'DCIR': ['','','','  ','','','','','','','','','','','','','','','','','',
                 '','','','','','    ','',' ','','','','                    ','','','',
                 '','',' ','              ',' ',''],
        'DSHL': ['','','','  ','','',' ',' ','','','','',' ','','               ',
                 '','                                  ',' ',''],
        'DMUT': ['','','','  ','','  ','  ','','',' ','','','','','',''],
        'DMOV': ['','','','  ',' ',' ',' ',' ',' ',' ','       ',
                 '                                   ',
                 '                                                                                        ',''],
        'DEOL': ['','','       ',' ','','','','',' ','',' ',' ',' ',' ',' ','',' ',
                 ' ','','','','','','    ',''],
        'DARE': ['  ','            ',''],
#        'CMNT': [''],
    }
        
    COD_EXEC_exception = ('TIPO', 'TITU', 'CMNT')   # códigos que não terminam em 99999 (valeu cepel!)
    
    for codExec in anaDict:
        aux = anaDict[codExec].values.tolist()
        
        ## converte list de list de varios types em list de list de str
        anaList = []
        for ind, line in enumerate(aux):
            result = map(str, aux[ind][:]) 
            anaList.append(list(result))
        
        ## aplica o fixedwidth para cada campo
        fwt = []
        for line in anaList:
            string = ""
            for j in range(0,len(line)):
                line[j] ='{dat:>{wid}}'.format(dat=line[j], wid=WIDTH[codExec][j])
                try:
                    string = string + line[j][:WIDTH[codExec][j]] + EMPTY[codExec][j]
                except:
                    string = string + line[j] + EMPTY[codExec][j]
            fwt.append(string)
        
        ## escreve o arquivo    
        with open(anaPath, 'a+') as file:
            file.write(codExec + '\n')
            for line in fwt:
                file.write(''.join(line) + '\n')
            if (codExec not in COD_EXEC_exception):
                file.write('99999\n')



# =============================================================================
# 
# =============================================================================