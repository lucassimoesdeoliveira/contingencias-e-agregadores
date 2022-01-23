# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 15:31:31 2020

@author: samir
"""
import pandas as pd
import numpy as np
import re
import epetoolbox as epe
import os
## Constantes
PATH_PWFS = r'./pwfs/'
regex = '[^\\/]+?(?=\.\w+$)'  
DICT_UF = {1:'AC',2:'AL',3:'AM',4:'AP',5:'BA',6:'CE',7:'DF',8:'ES',9:'GO',
            10:'MA',11:'MG',12:'MS',13:'MT',14:'PA',15:'PB',16:'PE',
            17:'PI',18:'PR',19:'RJ',20:'RN',21:'RO',22:'RR',23:'RS',
            24:'SC',25:'SE',26:'SP',27:'TO'}
DICT_CLASSIF = {1:'RB',2:'FRO',3:'DIS',4:'UEX',5:'DIT'}
DICT_TIPO = {np.nan:'',1:'CER',2:'EOL',3:'PCH',4:'SIN',5:'UHE',6:'UNE',
             7:'UTE',8:'UFV'}
DICT_GB = {'Z':999.0,'U':765.0,'T':525.0,'S':500.0,'R':440.0,'Q':345.0,
           'P':289.0,'O':230.0,'N':161.0,'M':138.0,'L':115.0,'K':88.0,
           'J':69.0,'H':34.5,'G':23.0,'F':20.0,'V':18.0,'E':14.4,'D':13.8,
           'C':13.2,'B':11.0,'A':6.9,'0':1.0}

def lista_obras(cod_exec, arqvs_analisados, IGNORE=[]):
    """
    Gera uma lista de barras/linhas do conjunto de pwfs (arqvs) passados.
    Essa lista registra onde aparece cada barra/linha em cada caso e infos 
    adicionais sobre a barra/linha para gerar a lista de contingência e o
    monitora.dat
    
    Args:
        path: caminho dos arquivos .pwf
        arqvs_analisados: list com arqvs analisados (não precisa ser contínua)
        cod_exec: 'DBAR' ou 'DLIN'
        IGNORE: list com número de barras a serem ignoradas na geração de 
        contingências 
        
    Returns:
        df: dataframe contendo informação de barras/linhas e info de em quais
        casos estão presentes.
        
    OBS:        
    """
    casos=[]
    for arqv in arqvs_analisados:
        pwf = epe.carrega_pwf(str(arqv))[cod_exec.upper()]
        if cod_exec.upper() == 'DBAR':
            pwf["V"] = pwf["Nome"].str[9:].astype(int)
            pwf = pwf[["Num","Nome","Gb","A1","A4","A5","V"]]
        elif cod_exec.upper() == 'DLIN':
            pwf = pwf[["De","Para","Nc","Tap","Cn","A1","A2"]]
            aux = list(pwf[['De','Para','Nc']].values)  #gera tuple id do circ
            pwf['id'] = [tuple(i) for i in aux]         #
        casos.append(pwf)
    ## gera um df com todas as barras/linhas de todos os casos
    df = casos[0]
    for caso in range(1, len(casos)):
        if cod_exec.upper() == 'DBAR': 
            aux = pd.merge(df, casos[caso], how='outer', left_on="Num",
                           right_on="Num", suffixes=["_x",""],
                           indicator="origem")
            aux = aux.loc[aux['origem']=='right_only'].drop(columns=['Nome_x',
                                   'Gb_x','A1_x','A4_x','A5_x','V_x','origem'])
            indexador = 'Num'
        elif cod_exec.upper() == 'DLIN':
            aux = pd.merge(df, casos[caso], how='outer', 
                           left_on=['De','Para','Nc'], 
                           right_on=['De','Para','Nc'],
                           suffixes=["_x",""],
                           indicator="origem")
            aux = aux.loc[aux['origem']=='right_only'].drop(columns=['Tap_x',
                                    'Cn_x','A1_x','A2_x','id_x','origem'])
            indexador = 'id'
        df = pd.concat([df,aux])
    df.reset_index(drop=True,inplace=True)
    ## identifica em uma variavel booleana a presença das barras em cada caso     
    for caso,arqv in zip(range(len(casos)),arqvs_analisados):
        aux = set(casos[caso][indexador])
        df[re.search(regex,arqv).group(0)] = df[indexador].isin(aux)
    ## remove barras/linhas no IGNORE
    if cod_exec.upper() == 'DBAR': 
        df = df.loc[-df['Num'].isin(IGNORE)]
    elif cod_exec.upper() == 'DLIN':
        df = df.loc[-((df['De'].isin(IGNORE)) | (df['Para'].isin(IGNORE)))]
        
    return df


def id_barrafict(dbar):
    """
    identifica barras fictícias de trafos de 3 enrolamentos. Usada para 
    numerar os trafos de 3enrol e nomear/fazer contingência apropriadamente.
    Args:
        dbar: dataframe com informações do DBAR
        
    Returns:
        dbar: dataframe com barras fictícias identificadas e trafos de 3 enrol
        numerados.
        
    OBS:        
    """
    dbar["fict"] = False
    dbar.loc[dbar["Nome"].str[9:]=="000", "fict"] = True
    
    def numera_fict(fict):
        if fict:
            numera_fict.cnt +=1
            return numera_fict.cnt
        else:
            return 0
        
    numera_fict.cnt = 0
    dbar["3e"] = dbar.apply(lambda row: numera_fict(row['fict']), axis=1)
    
    return dbar


def processa_dados_rede(dbar, dlin):
    """
    Combina dados de dlin e dbar, organiza e renomeia colunas dos df 
    resultantes, separa trafos e linhas em dois data frames, identifica o prim
    secn e terc de trafos de 2/3 enrolamentos.
    Args:
        dbar: dataframe com informações do DBAR
        dlin: dataframe com informações do DLIN
    Returns:
        dbar: dataframe com barras fictícias identificadas e trafos de 3 enrol
        numerados.
        
    OBS:        
    """    
    ## combina info de dbar com barras De do dlin
    dlin = pd.merge(dlin,
                    dbar[['Num','Nome','Gb','A1','A4','A5','V','fict','3e']],
                    how='left',left_on="De",right_on="Num")
    ## combina info de dbar com barras Para do dlin
    dlin = pd.merge(dlin,
                    dbar[['Num','Nome','Gb','A1','A4','A5','V','fict','3e']],
                    how='left',left_on="Para",right_on="Num")
    
    ## alterações cosméticas
    dlin["3e"] = dlin["3e_x"]+dlin["3e_y"]
    dlin.drop(columns=['Num_x','Num_y','A1','A1_y','3e_x','3e_y'],inplace=True)
    dlin.rename(columns={"A1_x": "UF_de",
                         "A2": "UF_para",
                         "Nome_x": "Nome_de",
                         "Gb_x": "Gb_de",
                         "A4_x": "Tipo_de",
                         "A5_x": "Class_de",
                         "fict_x": "Fict_de",
                         "V_x": "V_de",
                         "Nome_y": "Nome_para",
                         "Gb_y": "Gb_para",
                         "A4_y": "Tipo_para",
                         "A5_y": "Class_para",
                         "fict_y": "Fict_para",
                         "V_y": "V_para",
                         "3e": "#TF3e"},
                inplace=True)
    dbar.rename(columns={"A1": "UF",
                         "A4": "Tipo",
                         "A5": "Classif"},
                inplace=True)
    
    ## elimina códigos aplicando definições de dicionários
    dlin.loc[:,"UF_de"].replace(DICT_UF,inplace=True)
    dlin.loc[:,"UF_para"].replace(DICT_UF,inplace=True)
    dlin.loc[:,"Tipo_de"].replace(DICT_TIPO,inplace=True)
    dlin.loc[:,"Tipo_para"].replace(DICT_TIPO,inplace=True)
    dlin.loc[:,"Class_de"].replace(DICT_CLASSIF,inplace=True)
    dlin.loc[:,"Class_para"].replace(DICT_CLASSIF,inplace=True)
    dlin.loc[:,"Gb_de"].replace(DICT_GB,inplace=True)
    dlin.loc[:,"Gb_para"].replace(DICT_GB,inplace=True)
    
    dbar.loc[:,"UF"].replace(DICT_UF,inplace=True)
    dbar.loc[:,"Tipo"].replace(DICT_TIPO,inplace=True)
    dbar.loc[:,"Classif"].replace(DICT_CLASSIF,inplace=True)
    dbar.loc[:,"Gb"].replace(DICT_GB,inplace=True)
    
    dlin.reset_index(drop=True,inplace=True)
    
    ## separa a info de dlin em LTs e TRs
    dtrf = dlin.loc[-pd.isnull(dlin["Tap"])]
    dlin = dlin.loc[pd.isnull(dlin["Tap"])]
    
    ## identifica prim e secn para trafos de 2 enrolamentos
    def Vp(V1,V2):
        if V1==0:
            return V2
        if V2==0:
            return V1
        if V1>V2:
            return V1
        else:
            return V2
    def Vs(V1,V2):
        if V1==0:
            return 0
        if V2==0:
            return 0
        if V2>V1:
            return V1
        else:
            return V2
        
    dtrf["Vp"] = np.vectorize(Vp)(dtrf["V_de"],dtrf["V_para"])
    dtrf["Vs"] = np.vectorize(Vs)(dtrf["V_de"],dtrf["V_para"])
    
    ## identifica prim, secn e terc para trafos de 3 enrolamentos
    dtrf['Vt'] = None
    dtrf['Enrol'] = None
    
    for i in range(1, max(dtrf["#TF3e"])+1):
        aux = dtrf[["Vp","Cn"]].loc[dtrf["#TF3e"]==i]
        if not aux.empty and (len(aux)==3):
            enrol = 3*[2]
            enrol[np.argmax(aux['Vp'].values)] = 1
            enrol[np.argmin(aux['Vp'].values)] = 3
            aux['enrol'] = enrol
            aux.sort_values(by=['Vp','Cn'], ascending=False, inplace=True)
            buffer = pd.DataFrame({'Vp':[aux['Vp'].iloc[0]]*3, 
                                   'Vs':[aux['Vp'].iloc[1]]*3, 
                                   'Vt':[aux['Vp'].iloc[2]]*3, 
                                   'Enrol':aux['enrol']})
            dtrf.loc[dtrf["#TF3e"]==i, ["Vp","Vs","Vt","Enrol"]] = buffer
        # trafos de 3 enrol com só 2 enrol modelados (5 casos no PD)
        elif len(aux)==2: 
            enrol = 2*[2]
            enrol[np.argmax(aux['Vp'].values)] = 1
            enrol[np.argmin(aux['Vp'].values)] = 2
            aux['enrol'] = enrol
            aux.sort_values(by=['Vp','Cn'], ascending=False, inplace=True)
            buffer = pd.DataFrame({'Vp':[aux['Vp'].iloc[0]]*2, 
                                   'Vs':[aux['Vp'].iloc[1]]*2, 
                                   'Enrol':aux['enrol']})
            dtrf.loc[dtrf["#TF3e"]==i, ["Vp","Vs","Enrol"]] = buffer
            
    return (dbar, dlin, dtrf)


def filtragem(dbar, dlin, dtrf, uf, v_monitora, v_contingencia):
    """
    Filtra dados de dlin e dbar de acordo com uf, v_monitora e v_contingencia.
    Args:
        dbar: dataframe com informações do DBAR
        dlin: dataframe com informações do DLIN (apenas LTs)
        dtrf: dataframe com informações do DLIN (apenas TRs)
        uf: list com UF's de interesse
        v_monitora: set com tensões de barras a serem monitoradas (RB+distr)
        v_contingencia: set com tensões de barras a serem contingenciadas (RB)
    Returns:
        dbar: dataframe dbar filtrado.
        dlin: dataframe dlin filtrado.
        dtrf: dataframe dtrf filtrado.
        
    OBS:        
    """ 
    ## por UF
    dbar = dbar.loc[dbar['UF'].isin(uf)]
    dlin = dlin.loc[(dlin['UF_de'].isin(uf)) | (dlin['UF_para'].isin(uf))]
    dtrf = dtrf.loc[(dtrf['UF_de'].isin(uf)) | (dtrf['UF_para'].isin(uf))]
    
    ## por tensão
    V = v_monitora | v_contingencia

    dbar = dbar.loc[dbar['V'].isin(V)]  
    # dbar = dbar.loc[-((dbar['UF']!='MG') & (dbar['V']<230))]  
    
    dlin = dlin.loc[(dlin['V_de'].isin(V))]
    # dlin = dlin.loc[(dlin['V_de']>=138)] ## apenas LTs de V>138kV
    # dlin = dlin.loc[-(((dlin['UF_de']!='MG') & 
    #                   (dlin['UF_para']!='MG')) & 
    #                   (dlin['V_de']<230))]  ## retira LTs que não estão
    #                                         ## ou vão pra MG e não são RB
    
    dtrf = dtrf.loc[(dtrf['Vp'].isin(V))] # filtra trafos por Vp
    # dtrf = dtrf.loc[-(dtrf['Vs']<138)]    # tira todo trafo com Vs<138kV 
    # dtrf = dtrf.loc[-(((dtrf['UF_de']!='MG') & 
    #                   (dtrf['UF_para']!='MG')) &
    #                   (dtrf['Vs']<138))]
    
    dtrf = dtrf.loc[-((dtrf['Class_de'].isin(['UEX'])) |
                      (dtrf['Class_para'].isin(['UEX'])))] #filtra TR de usina
    dtrf = dtrf.loc[(dtrf['Enrol'].isin([None, 1]))]
    
    return (dbar, dlin, dtrf)

    
def define_monitora(dbar, dlin, dtrf):
    """
    Organiza dados dos dataframes de barras/LTs/TRs para passar a função que 
    escreve o arquivo monitora.dat. Também gera o nome das contingências e 
    barras.
    Args:
        dbar: dataframe com informações do DBAR
        dlin: dataframe com informações do DLIN (apenas LTs)
        dtrf: dataframe com informações do DLIN (apenas TRs)
    Returns:
        dLT: dataframe dlin com apenas colunas necessárias ao arqv de conting.
        dTR: dataframe dtrf com apenas colunas necessárias ao arqv de conting.
        circs: dataframe com dados necessários ao arqv monitora .dat.
        
    OBS:        
    """ 
    ## separa trafos de 2 e 3 enrol
    # filtra só linha do enrol prim de trafos de 3 enrol (pra contingência)
    dtrf3 = dtrf.loc[(dtrf['Enrol'].isin([1]))]      
    dtrf2 = dtrf.loc[(dtrf['Enrol'].isin([None]))]   # filtra só trf 2enrol
    
    ## sumariza informações
    dLT = dlin.drop(columns=['Tap','Cn','UF_para','id','Gb_de','Tipo_de',
                             'Class_de','Fict_de','Gb_para','UF_de',
                             'Tipo_para','Class_para','V_para','Fict_para',
                             '#TF3e'])
    dTR2 = dtrf2.drop(columns=['Tap','Cn','UF_para','id','Gb_de','Tipo_de',
                               'Class_de','V_de','Fict_de','Gb_para','UF_de',
                               'Tipo_para','Class_para','V_para','Fict_para',
                               '#TF3e','Vt','Enrol'])
    dTR3 = dtrf3.drop(columns=['Tap','Cn','UF_para','id','Gb_de','Tipo_de',
                               'Class_de','V_de','Fict_de','Gb_para','UF_de',
                               'Tipo_para','Class_para','V_para','Fict_para',
                               '#TF3e','Vt','Enrol'])
    dTR = pd.concat([dTR2,dTR3])
    dBUS = dbar.drop(columns=['Gb','UF','Tipo','Classif','V','fict','3e']) 

    dLT['V_de'] = dLT['V_de'].astype('int64')
    dTR[['Vp','Vs']] = dTR[['Vp','Vs']].astype('int64')
    
    ## compõe o nome das contingências de LTs e TR
    LT = ('LT ' + dLT['V_de'].map(str) + 'kV ' + dLT['Nome_de'] + ' - ' 
          + dLT['Nome_para'] + ' - C' + dLT['Nc'].map(str))
    TR2 = (dTR2['Nc'].map(str) + 'ºTF ' + dTR2['Vp'].map(int).map(str) + '/' 
           + dTR2['Vs'].map(int).map(str) + 'kV ' + dTR2['Nome_de'] + ' - ' 
           + dTR2['Nome_para'])
    TR3 = ('TF ' + dTR3['Vp'].map(int).map(str) + '/' 
           + dTR3['Vs'].map(int).map(str) 
           + 'kV ' + dTR3['Nome_de'] + ' - ' + dTR3['Nome_para'])
    TR = pd.concat([TR2, TR3])

    ## escreve o monitora.dat
    ignore_tipo = ['CAP','TAP']  # não põe barras fictícias no monitora.dat

    barras = dBUS[['Num']].loc[-dBUS['Nome'].str.slice(6,9).isin(ignore_tipo)]
    barras['Vmn'] = ''
    barras['Vmx'] = ''
    barras['Titulo'] = dBUS['Nome']
    barras.rename(columns={"Num": "Nb", "Nome": "Titulo"});
    
    circs = pd.concat([dLT, dTR],sort=False).reset_index(drop=True)
    circs['Sin'] = ''
    circs['Texto_1'] = ''
    circs['Texto_2'] = ''
    circs['flag_carreg'] = ''
    circs['Cn1'] = ''
    circs['Cn2'] = ''
    circs['Cn3'] = ''
    circs['Cn4'] = ''
    circs['Cn5'] = ''
    circs['Cn6'] = ''
    circs['Cn7'] = ''
    circs['Titulo'] = pd.concat([LT,TR],sort=False).values
    
    mon_dict = {'DBTB': [],
           'DFTB': []} 
    mon_dict['DBTB'] = barras
    mon_dict['DFTB'] = circs[['De','Para','Nc','Sin','Texto_1','Texto_2',
                             'flag_carreg','Cn1','Cn2','Cn3','Cn4','Cn5',
                             'Cn6','Cn7','Titulo']]
    
    try:
        os.mkdir('./contingencias/')
    except OSError:
        pass
    try:
        os.remove(r".\contingencias\monitora.DAT")
    except OSError:
        pass    
    
    epe.escreve_monitora(mon_dict, mon_path = r".\contingencias\monitora.DAT")
    
    return (dLT, dTR, circs)
    

def escreve_tabela_conting(dLT, dTR, circs, v_contingencia, arqvs_analisados):
    """
    Escreve a tabela de contingências no formato PAD e REDE.
    Args:
        dLT: dataframe dlin com apenas colunas necessárias ao arqv de conting.
        dTR: dataframe dtrf com apenas colunas necessárias ao arqv de conting.
        circs: dataframe com dados necessários ao arqv monitora .dat.
        v_contingencia: set com tensões de barras a serem contingenciadas (RB)
    Returns: None      
    OBS:        
    """ 
    dLTx = dLT.loc[dLT['V_de'].isin(v_contingencia)]
    dLTx.drop(columns=['De','Para','Nc','V_de','Nome_de','Nome_para'],
              inplace=True)
    dLTx.replace({True: 'x', False: ''},inplace=True)
    dTRx = dTR.loc[dTR['Vp'].isin(v_contingencia)]
    dTRx.drop(columns=['De','Para','Nc','Vp','Vs','Nome_de','Nome_para'],
              inplace=True)
    dTRx.replace({True: 'x', False: ''},inplace=True)
    dTRx.reset_index(drop=True,inplace=True)
    
    tab_conting = circs.loc[circs['V_de'].isin(v_contingencia) | 
                      circs['Vp'].isin(v_contingencia)].reset_index(drop=True)
    tab_conting = tab_conting[['Titulo','De','Para','Nc']]
    tab_conting = pd.concat([tab_conting, 
                        pd.concat([dLTx,dTRx]).reset_index(drop=True)],axis=1)
    ## versão REDE
    arqvs = [re.search(regex,arqv).group(0) for arqv in arqvs_analisados]
    tab_conting['REDE'] = ''
    for arqv in arqvs:
        tab_conting['REDE'].loc[tab_conting.iloc[:][arqv]=='x'] =  \
                                          tab_conting['REDE'] + str(arqv) + ';' 
    try:
        os.remove(r'.\contingencias\tabela_contingências.xlsx')
    except OSError:
        pass
    
    with pd.ExcelWriter(r'.\contingencias\tabela_contingências.xlsx') as writer:  
        tab_conting.drop('REDE', axis=1).to_excel(writer,
                                                  sheet_name='Copiar no PAD')                                             
        tab_conting[['Titulo','De','Para','Nc','REDE']].to_excel(writer, 
                                                  sheet_name='Copiar no REDE')

    return None


if __name__ == '__main__':   
    ## Entradas
    uf = ['RJ','ES'] 
    v_monitora = {500,440,345,230,138}
    v_contingencia = {500,440,345,230}
    arqvs_analisados = ['./pwfs/first.pwf','./pwfs/second.pwf',
                        './pwfs/third.pwf','./pwfs/fourth.pwf',
                        './pwfs/fifth.pwf'] #range(1,6) #[24,26,28,30]
    IGNORE = [5190,5191,5192,5193,5194,5195,5196,5197,5200,5201,5205,38863,
              38864,41973,42158,42159,42160,4947,5206,4943,60189,4479,4480,
              60242,60241,60211,60213,60214,] # Jirau, S.Antônio, Elos CC, etc
    
    ## Execução
    import time
    start_time = time.time()
    dbar = lista_obras('DBAR', arqvs_analisados, IGNORE)
    print("dbar: %ss" % (time.time() - start_time))
    
    start_time = time.time()
    dlin = lista_obras('DLIN', arqvs_analisados, IGNORE)
    print("dlin: %ss" % (time.time() - start_time))
    
    start_time = time.time()
    dbar = id_barrafict(dbar)
    print("fict: %ss" % (time.time() - start_time))
    
    start_time = time.time()
    dbar, dlin, dtrf = processa_dados_rede(dbar, dlin)
    print("proc: %ss" % (time.time() - start_time))
    
    start_time = time.time()
    dbar, dlin, dtrf = filtragem(dbar, dlin, dtrf, uf, v_monitora,
                                  v_contingencia)
    print("filt: %ss" % (time.time() - start_time))
    
    start_time = time.time()
    dLT, dTR, circs = define_monitora(dbar, dlin, dtrf)
    print("monit: %ss" % (time.time() - start_time))
    
    start_time = time.time()
    escreve_tabela_conting(dLT, dTR, circs, v_contingencia, arqvs_analisados)
    print("conting: %ss" % (time.time() - start_time))
    
    
    