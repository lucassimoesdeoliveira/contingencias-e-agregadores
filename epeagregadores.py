# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 21:10:48 2020

@author: Samir
"""
import os
import subprocess
import pandas as pd
import numpy as np
import epetoolbox as epe


def gen_agregadores(dbar, dlin, regioes=True, geracao=True, gera_dlin=True):
    """
    Usa os dados de Barra e Linha para atribuir agregadores às barras e linhas
    A1: UF_De (27 UFs)
    A2: UF_Para (27 UFs),
    A3: Região (N, NE, CO, SE, S)
    A4: Tipo Geração (CER, EOL, PCH, SIN, UHE, UTE, UFV),
    A5: Classificação Instalação (Rede Básica, Distribuição,
                                  Uso Exclusivo, DIT)

    Args:
        dbar: pandas DataFrame com dados de barras
        dlin: pandas DataFrame com dados de linhas
        regioes: bool indicando a opção de gerar dados de regiões (A3)
        geracao: bool indicando a opção de gerar dados de geracao (A4)
        gera_dlin: bool indicando a opção de gerar dados de dlin

    Returns:
        dbar, dlin: pandas DataFrames com campos de agregadores preenchidos

    Raises:
        #TODO
    """
    tradutor_estados = pd.DataFrame({
        'estado': ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO',
                   'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR',
                   'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'],
        'estado_cod': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                       16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
        'regiao_get': ['N', 'NE', 'N', 'N', 'NE', 'NE', 'CO', 'SE', 'CO',
                       'N', 'SE', 'SE', 'CO', 'N', 'NE', 'NE', 'NE', 'S',
                       'SE', 'NE', 'N', 'N', 'S', 'S', 'NE', 'SE', 'N'],
        'regiao_get_cod': [1, 2, 1, 1, 2, 2, 3, 4, 3, 1, 4, 4, 3, 1, 2,
                           2, 2, 5, 4, 2, 1, 1, 5, 5, 2, 4, 1],
        'regiao': ['N', 'NE', 'N', 'N', 'NE', 'NE', 'CO', 'SE', 'CO', 'NE',
                   'SE', 'CO', 'CO', 'N', 'NE', 'NE', 'NE', 'S', 'SE', 'NE',
                   'N', 'N', 'S', 'S', 'NE', 'SE', 'N'],
        'regiao_cod':[1, 2, 1, 1, 2, 2, 3, 4, 3, 2, 4, 3, 3, 1, 2, 2, 2, 5, 4,
                      2, 1, 1, 5, 5, 2, 4, 1]

    })

    tradutor_tipo_geracao = pd.DataFrame({
        'Sigla': ['CER', 'EOL', 'PCH', 'SIN', 'UHE', 'UNE', 'UTE', 'UFV'],
        'Cod': [1, 2, 3, 4, 5, 6, 7, 8]
    })


    tradutor_classificacao_barra = pd.DataFrame({
        'Sigla': ['Rede Básica',
                  'Fronteira',
                  'Distribuição',
                  'Uso Exclusivo',
                  'DIT'],
        'Cod': [1, 2, 3, 4, 5]
    })

    # dbar_estados contem todas as barras que possuem nos espaços 7 e 8 do
    # Nome valoes contidos em tradutor_estados

    dbar.loc[dbar['Nome'].str[7:9].isin(tradutor_estados['estado']), 'A1'] = dbar['Nome'].str[7:9]

    # Removendo o agregador de UF das barras que tem CAP e TAP no nome
    # Capacitores e Tapes estavam sendo marcadas no Amapá
    dbar.loc[dbar['Nome'].str[6:9] == 'CAP', 'A1'] = np.nan
    dbar.loc[dbar['Nome'].str[6:9] == 'TAP', 'A1'] = np.nan

    # CRIANDO TABELA VERDADE VIZINHANÇA
    a = dlin[['De', 'Para', 'Nc', 'X']].merge(dbar[['Num', 'Nome']],
                                              how='left',
                                              left_on='De',
                                              right_on='Num')
    a = a.merge(dbar[['Num', 'Nome']],
                how='left',
                left_on='Para',
                right_on='Num')

    a.rename(columns={'Nome_x': 'Nome_De',
                      'Nome_y': 'Nome_Para'},
             inplace=True)

    a.drop(['Num_x', 'Num_y'], axis=1, inplace=True)

    a.loc[a['Nome_De'].str[7:9].isin(tradutor_estados['estado']), 'UF_De'] = a['Nome_De'].str[7:9]
    a.loc[a['Nome_Para'].str[7:9].isin(tradutor_estados['estado']), 'UF_Para'] = a['Nome_Para'].str[7:9]

    a.loc[(a['Nome_De'].str[6:9] == 'CAP') | (a['Nome_De'].str[6:9] == 'TAP'), 'UF_De'] = np.nan
    a.loc[(a['Nome_Para'].str[6:9] == 'CAP') | (a['Nome_Para'].str[6:9] == 'TAP'), 'UF_Para'] = np.nan

    a.loc[a.UF_De.isnull(), 'UF_De'] = a.loc[a.UF_De.isnull(), 'UF_Para']
    a.loc[a.UF_Para.isnull(), 'UF_Para'] = a.loc[a.UF_Para.isnull(), 'UF_De']

    df1 = a[['De', 'UF_De', 'X']].copy()
    df1.rename(columns={'De': 'Num', 'UF_De': 'UF'}, inplace=True)
    df2 = a[['Para', 'UF_Para', 'X']].copy()
    df2.rename(columns={'Para': 'Num', 'UF_Para': 'UF'}, inplace=True)

    df3 = pd.concat([df1, df2], ignore_index=True)
    df3.sort_values(by=['Num', 'X'], inplace=True)

    df4 = df3.dropna().drop_duplicates('Num', keep='first')

    dbar.loc[(dbar.A1.isnull()) & (dbar.Num.isin(df4.Num)), ['A1']] = df4.loc[df4.Num.isin(dbar.loc[dbar.A1.isnull()].Num), 'UF'].values

    dbar_1_viz_De = dbar[['Num', 'Nome']].merge(dlin[['De', 'Para']],
                                                how='outer',
                                                left_on='Num',
                                                right_on='De')
    dbar_1_viz_De.drop(['De'], axis=1, inplace=True)

    dbar_1_viz_Para = dbar[['Num', 'Nome']].merge(dlin[['De', 'Para']],
                                                  how='outer',
                                                  left_on='Num',
                                                  right_on='Para')
    dbar_1_viz_Para.drop(['Para'], axis=1, inplace=True)

    dbar_1_viz_De.rename(columns={'Para': '1oViz'}, inplace=True)
    dbar_1_viz_Para.rename(columns={'De': '1oViz'}, inplace=True)

    dbar_1_viz = pd.concat([dbar_1_viz_De, dbar_1_viz_Para], ignore_index=True)
    dbar_1_viz.sort_values(by=['Num'], inplace=True)

    dbar_1_viz = dbar_1_viz.dropna()

    dbar_2_viz = dbar_1_viz.merge(dbar_1_viz,
                                  how='left',
                                  left_on='1oViz',
                                  right_on='Num')

    dbar_2_viz.drop(['Nome_x', '1oViz_x', 'Num_y', 'Nome_y'],
                    axis=1,
                    inplace=True)

    dbar_2_viz.rename(columns={'Num_x': 'Num', '1oViz_y': '2oViz', },
                      inplace=True)


    dbar_1_viz_T = pd.merge(dbar_1_viz, dbar[['Num', 'A1']],
                            left_on='1oViz',
                            right_on='Num')

    b = dbar_1_viz_T[dbar_1_viz_T.Num_x.isin(dbar_1_viz_T[dbar_1_viz_T.A1.isnull()].Num_y)]
    c = b.dropna().drop_duplicates()


    dbar = dbar.merge(c[['Num_x', 'A1']],
                      how='left',
                      left_on='Num',
                      right_on='Num_x')

    dbar['A1_x'] = dbar['A1_x'].fillna(dbar['A1_y'])
    dbar.drop(['Num_x', 'A1_y'], axis=1, inplace=True)
    dbar.rename(columns={'A1_x': 'A1'}, inplace=True)

    # Repetindo barras remanecentes

    dbar_1_viz_De = dbar[['Num', 'Nome']].merge(dlin[['De', 'Para']],
                                                how='outer',
                                                left_on='Num',
                                                right_on='De')
    dbar_1_viz_De.drop(['De'], axis=1, inplace=True)
    dbar_1_viz_Para = dbar[['Num', 'Nome']].merge(dlin[['De', 'Para']],
                                                  how='outer',
                                                  left_on='Num',
                                                  right_on='Para')
    dbar_1_viz_Para.drop(['Para'], axis=1, inplace=True)



    dbar_1_viz_De.rename(columns={'Para': '1oViz'}, inplace=True)
    dbar_1_viz_Para.rename(columns={'De': '1oViz'}, inplace=True)



    dbar_1_viz = pd.concat([dbar_1_viz_De, dbar_1_viz_Para], ignore_index=True)
    dbar_1_viz.sort_values(by=['Num'], inplace=True)

    dbar_1_viz = dbar_1_viz.dropna()

    dbar_2_viz = dbar_1_viz.merge(dbar_1_viz,
                                  how='left',
                                  left_on='1oViz',
                                  right_on='Num')

    dbar_2_viz.drop(['Nome_x', '1oViz_x', 'Num_y', 'Nome_y'],
                    axis=1,
                    inplace=True)
    dbar_2_viz.rename(columns={'Num_x': 'Num', '1oViz_y': '2oViz'},
                      inplace=True)


    dbar_1_viz_T = pd.merge(dbar_1_viz, dbar[['Num', 'A1']],
                            left_on='1oViz',
                            right_on='Num')

    b = dbar_1_viz_T[dbar_1_viz_T.Num_x.isin(dbar_1_viz_T[dbar_1_viz_T.A1.isnull()].Num_y)]
    c = b.dropna().drop_duplicates()


    dbar = dbar.merge(c[['Num_x', 'A1']],
                      how='left',
                      left_on='Num',
                      right_on='Num_x')

    dbar['A1_x'] = dbar['A1_x'].fillna(dbar['A1_y'])
    dbar.drop(['Num_x', 'A1_y'], axis=1, inplace=True)
    dbar.rename(columns={'A1_x': 'A1'}, inplace=True)

    # =========================================================================
    # Atribuindo regiões (N, NE, CO, SE, S) às barras
    if regioes:
        dbar['A3'] = dbar['A1']
    # =========================================================================

    # =========================================================================
    # Atribuindo tipos barras - de acordo com os caracteres 7, 8 e 9 do campo Nome
    if geracao:
        dbar.loc[dbar['Nome'].str[6:9].isin(tradutor_tipo_geracao['Sigla']), 'A4'] = dbar['Nome'].str[6:9]
    # ==========================================================================

    # ==========================================================================
    # Atribuindo classificação das barras de acordo com o nível de tensão, usando os caracteres 10, 11 e 12
    dbar['tensao'] = pd.to_numeric(dbar['Nome'].str[9:13], errors='coerce')
    #dbar.drop(['tensao'], axis=1, inplace=True)


    # =========================================================================

    # Agregadores para o DLIN
    # =========================================================================

    if gera_dlin:
        temp = dlin

        match_de = pd.merge(dlin, dbar,
                            left_on='De',
                            right_on='Num',
                            how='left')

        match_de['A1_x'] = match_de['A1_y']
        match_de = match_de.rename(columns={'A1_x': 'A1'})
        temp['A1'] = match_de['A1']

        match_para = pd.merge(dlin, dbar,
                              left_on='Para',
                              right_on='Num',
                              how='left')

        match_para['A1_x'] = match_para['A1_y']
        match_para = match_para.rename(columns={'A1_x': 'A1'})
        temp['A2'] = match_para['A1']

        # Usando apenas as linhas que estão contidas dentro de um mesmo estado,
        # para não criar outro agregador

        temp2 = pd.merge(dlin, temp, on=['De', 'Para', 'Nc'], how='left')

        dlin['A1'] = temp2['A1_y']
        dlin['A2'] = temp2['A2_y']



        # CRIANDO TABELA VERDADE VIZINHANÇA
        b = dlin[['De', 'Para', 'Nc', 'Tap']].merge(dbar[['Num', 'tensao']],
                                                    how='left',
                                                    left_on='De',
                                                    right_on='Num')
        b = b.merge(dbar[['Num', 'tensao']],
                    how='left',
                    left_on='Para',
                    right_on='Num')

        b.rename(columns={'tensao_x': 'Tensao_De',
                          'tensao_y': 'Tensao_Para'},
                 inplace=True)

        b.drop(['Num_x', 'Num_y'], axis=1, inplace=True)

        b.dropna(axis=0, subset=['Tap'], inplace=True)

        b.loc[(b.Tensao_De >= 230) & \
              (b.Tensao_Para < 230) | \
              (b.Tensao_De < 230) & \
              (b.Tensao_Para >= 230), 'Tipo'] = 'Fronteira'

        df1 = b[['De', 'Tipo']].copy()
        df1.rename(columns={'De': 'Num'}, inplace=True)
        df2 = b[['Para', 'Tipo']].copy()
        df2.rename(columns={'Para': 'Num'}, inplace=True)

        df3 = pd.concat([df1, df2], ignore_index=True)
        df3.sort_values(by=['Tipo', 'Num'], inplace=True)

        df4 = df3.dropna().drop_duplicates('Num', keep='first')


        b = dlin[['De', 'Para', 'Nc', 'Tap']].merge(df4[['Num', 'Tipo']],
                                                    how='left',
                                                    left_on='De',
                                                    right_on='Num')

        b = b.merge(df4[['Num', 'Tipo']],
                    how='left',
                    left_on='Para',
                    right_on='Num')

        b.rename(columns={'Tipo_x': 'Tipo_De', 'Tipo_y': 'Tipo_Para'},
                 inplace=True)
        b.drop(['Num_x', 'Num_y'], axis=1, inplace=True)

        b.dropna(axis=0, subset=['Tap'], inplace=True)


        b.loc[b.Tipo_De.isnull(), 'Tipo_De'] = b.loc[b.Tipo_De.isnull(), 'Tipo_Para']
        b.loc[b.Tipo_Para.isnull(), 'Tipo_Para'] = b.loc[b.Tipo_Para.isnull(), 'Tipo_De']


        df1 = b[['De', 'Tipo_De']].copy()
        df1.rename(columns={'De': 'Num', 'Tipo_De': 'Tipo'}, inplace=True)
        df2 = b[['Para', 'Tipo_Para']].copy()
        df2.rename(columns={'Para': 'Num', 'Tipo_Para': 'Tipo'}, inplace=True)

        df3 = pd.concat([df1, df2], ignore_index=True)
        df3.sort_values(by=['Tipo', 'Num'], inplace=True)

        df4 = df3.dropna().drop_duplicates('Num', keep='first')



        dbar.loc[(dbar.tensao < 230) & (dbar.Num.isin(df4.Num)), ['A5']] = df4.loc[df4.Num.isin(dbar.loc[dbar.tensao < 230].Num), 'Tipo'].values
        dbar.loc[(dbar.tensao >= 230) & (dbar.A5.isnull()), ['A5']] = 'Rede Básica'
        dbar.loc[(dbar.tensao < 230) & (dbar.A5.isnull()), ['A5']] = 'Distribuição'

        dbar.loc[(dbar.tensao < 230) & (dbar.A4.notnull()), ['A5']] = 'Uso Exclusivo'

        dfDITs = {8197, 8200, 8220, 38948, 38972, 8260, 18503, 18504, 18510,  
        10331, 8285, 8290, 8292, 6245, 103, 8300, 115, 120, 18553, 20600, 
        6265, 127, 131, 6278, 8328, 39051, 144, 2193, 151, 51353, 10401, 6306,
        162, 8358, 51367, 169, 10417, 10418, 183, 186, 188, 39101, 8384, 192,
        39111, 39112, 39113, 4306, 2261, 4317, 4325, 30952, 30953, 51439, 
        12529, 6393, 51461, 10504, 10511, 26914, 26915, 26919, 12602, 10567,
        18761, 18763, 8529, 2392, 6490, 4460, 8561, 370, 4471, 51699, 2575,
        6527, 6528, 6545, 2449, 12699, 445, 6606, 6607, 51698, 35352, 2627, 
        560, 561, 2612, 2614, 2616, 19002, 2619, 2621, 2623, 6721, 6722, 671,
        2629, 2631, 2633, 586, 2635, 2637, 2639, 2642, 2646, 600, 2650, 653, 
        2654, 607, 2658, 2660, 615, 12904, 617, 618, 619, 620, 621, 2667, 622, 
        625, 2674, 624, 2676, 629, 2678, 631, 630, 633, 627, 632, 636, 19069,           
        639, 640, 2684, 638, 643, 644, 642, 646, 647, 648, 649, 650, 651, 4741,          
        654, 655, 2704, 656, 658, 657, 660, 661, 2709, 663, 664, 665, 668, 670,            
        672, 673, 6818, 674, 676, 675, 19110, 679, 677, 680, 6826, 682, 2732,             
        686, 687, 683, 688, 6834, 690, 692, 693, 691, 695, 2744, 2745, 696,               
        698, 2751, 708, 2757, 2762, 6861, 6862, 15054, 15056, 15055, 6863, 685,            
        6868, 2772, 2774, 6870, 2776, 2778, 13018, 745, 746, 6894, 2800, 752,            
        10998, 6903, 15100, 6910, 2817, 2818, 6925, 2840, 800, 810, 811, 812,             
        13102, 814, 819, 6964, 6965, 820, 9021, 6981, 6984, 843, 2902, 2903,            
        2907, 2908, 862, 2912, 2914, 15203, 2916, 9061, 15204, 15205, 7011,          
        2922, 2918, 2924, 2927, 7028, 2935, 2936, 9082, 2938, 9084, 9085,                 
        2944, 2945, 2947, 2949, 2950, 2953, 2955, 5005, 2958, 7055, 909, 2960,           
        39842, 39849, 7081, 943, 7090, 7091, 948, 976, 7122, 7126, 7128, 7129,            
        9194, 52208, 9212, 9218, 9220, 9221, 9228, 9234, 7188, 9244, 616,                 
        9253, 7207, 19501, 9262, 9263, 9267, 9270, 623, 19519, 19523, 9284,              
        19546, 19547, 17501, 17502, 46201, 46203, 637, 25735, 9356, 9358, 9360,         
        9364, 9371, 9372, 9376, 1192, 9384, 9388, 9389, 9395, 9396, 9397, 9398,        
        9400, 1214, 25795, 7367, 7369, 1229, 7379, 1238, 7383, 7386, 1252,          
        9452, 11501, 11517, 9470, 27913, 1291, 3340, 3339, 2701, 1317, 19760,             
        1331, 1335, 9527, 7484, 7491, 9542, 1351, 9554, 678, 7514, 1376, 11618,           
        1380, 681, 9574, 7536, 3444, 1413, 1419, 1420, 7566, 7571, 3475, 7576,            
        9626, 7578, 11673, 7580, 7582, 1439, 9632, 7583, 9634, 7585, 9636,          
        9639, 7589, 9642, 1450, 7596, 9645, 9646, 7600, 7603, 9652, 9658, 9661,          
        7631, 3563, 3579, 1547, 1566, 3618, 7717, 7718, 42541, 1582, 7728,         
        7738, 7742, 42559, 9792, 7746, 42562, 42566, 42571, 9805, 42574, 1618,          
        5723, 7777, 1647, 44656, 44659, 7795, 1653, 1654, 7796, 7803, 7804,         
        1667, 3721, 1673, 1675, 7821, 1680, 7825, 3730, 7833, 1695, 3747, 3749,          
        1710, 3760, 3770, 3771, 3779, 3786, 1744, 1746, 7901, 3811, 3818, 1780,          
        1783, 12033, 46852, 46854, 3851, 10001, 10007, 1817, 1824, 10019, 1827,          
        1831, 1832, 7983, 44850, 3897, 8012, 3921, 1873, 1874, 26457, 8030,         
        8037, 46949, 44905, 3948, 26477, 44913, 26482, 10099, 3955, 26481,         
        8059, 8060, 8061, 26491, 10111, 8066, 8090, 49051, 8101, 30649, 6081,         
        8130, 8139, 8143, 6100, 12246, 2008, 14308, 8180, 38907, 602, 603,
        6082, 3961, 8058, 3937, 3877, 5876, 3750, 7809, 1622, 1587, 7735, 1487,
        7587, 7588, 17007, 7577, 11619, 3301, 3302, 19762, 9399, 1168, 1168, 
        1168, 699, 697, 21116, 15230, 2940, 17443, 7204, 626, 628, 988,  9111,
        6867, 2803, 6957, 2905, 2921, 6724, 8280}
        # dfDITs = pd.read_excel(r'./_temp/DITS AEGE.xlsx')
        # dfDITs.rename(columns={'Nº Barra PD': 'Num'}, inplace=True)
        # dfDITs['Num'] = pd.to_numeric(dfDITs['Num'], errors='coerce')
        # dbar.loc[(dbar.Num.isin(dfDITs.Num)), 'A5'] = 'DIT'
        
        dbar.loc[(dbar.Num.isin(dfDITs)), 'A5'] = 'DIT'

        dlin.loc[dlin.A1.isnull(), 'A1'] = dlin.loc[dlin.A1.isnull(), 'A2']
        dlin.loc[dlin.A2.isnull(), 'A2'] = dlin.loc[dlin.A2.isnull(), 'A1']

    dict_uf_cod = dict(tradutor_estados[['estado', 'estado_cod']].to_dict('split')['data'])
    dict_uf_regiao = dict(tradutor_estados[['estado', 'regiao_cod']].to_dict('split')['data'])
    dict_geracao_cod = dict(tradutor_tipo_geracao[['Sigla', 'Cod']].to_dict('split')['data'])
    dict_classificacao_barra = dict(tradutor_classificacao_barra[['Sigla', 'Cod']].to_dict('split')['data'])

    dbar.replace(to_replace={'A1': dict_uf_cod,
                             'A3': dict_uf_regiao,
                             'A4': dict_geracao_cod,
                             'A5': dict_classificacao_barra},
                 value=None,
                 inplace=True)

    dlin.replace(to_replace={'A1': dict_uf_cod,
                             'A2': dict_uf_cod},
                 value=None,
                 inplace=True)

    return dbar, dlin
    
def saida_pwf_agregadores(dbar, dlin, nome):
    """
    Cria um arquivo .pwf com as modificações necessárias para
    adicionar os dados de agregadores ao caso Anarese

    Args:
        dbar: pandas DataFrame com os dados de barra (com agregadores)
        dlin: pandas DataFrame com os dados de linha (com agregadores)
        nome: nome do arquivo a ser criado

    Returns:
        Cria um arquivo .pwf com as modificações necessárias para
        adicionar os dados de agregadores ao caso Anarese

    Raises:
        #TODO
    """
    dbar = dbar[['Num', 'O', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6']]
    dbar = dbar.sort_values(by='Num')

    dbar['O'] = 'M'
    dbar['O'] = dbar['O'].map('{:.1s}'.format)

    format_cols = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6']
    dbar[format_cols] = dbar[format_cols].applymap('{:.0f}'.format)

    dbar = dbar.replace(to_replace='nan', value='   ')

    o_espacos = '%1s' + ' '*75

    np.savetxt(nome + '.pwf',
               dbar,
               fmt=('%5.f', o_espacos, '%3s', '%3s', '%3s', '%3s', '%3s', '%3s'),
               header='DBAR\n(Num)OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)M(1)(2)(3)(4)(5)(6)(7)(8)(9)(10',
               footer='99999',
               comments='',
               delimiter='')
    # gerando agregadores do DLIN

    dlin = dlin[['De', 'O', 'Para', 'Nc', 'A1', 'A2']]
    dlin = dlin.sort_values(by='De')

    dlin['O'] = 'M'
    dlin['O'] = dlin['O'].map('{:.1s}'.format)

    format_cols = ['A1', 'A2']
    dlin[format_cols] = dlin[format_cols].applymap('{:.0f}'.format)

    dlin = dlin.replace(to_replace='nan', value='   ')

    o_espacos = ' '*2 + '%1s' + ' '*2
    nc_espacos = '%2.f' + ' '*61

    # usando o f_handle para abrir o arquivo já existente - criado pelo dbar - e adicionar os dados do dlin
    with open(nome + '.pwf', 'a') as f_handle:
        np.savetxt(f_handle,
                   dlin,
                   fmt=('%5.f', o_espacos, '%5.f', nc_espacos, '%3s', '%3s'),
                   header='DLIN\n(De )d O d(Pa )NcEP ( R% )( X% )(Mvar)(Tap)(Tmn)(Tmx)(Phs)(Bc  )(Cn)(Ce)Ns(Cq)(1)(2)(3)(4)(5)(6)(7)(8)(9)(10',
                   footer='99999\nFIM',
                   comments='',
                   delimiter='')


def gera_pwf_agregadores(files, nomes):
    ''' Calcula e exporta dados de agregadores '''
       
    for f,name in zip(files,nomes):
        df = epe.carrega_pwf(f)
        dbar = df['DBAR']
        dlin = df['DLIN']
        # limpando agregadores antigos
        cols = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10']
        dbar[cols] = np.nan
        dlin[cols] = np.nan

        dbar, dlin = gen_agregadores(dbar, dlin, regioes=True,
                                         geracao=True)
        
        saida_pwf_agregadores(dbar, dlin,
                                  nome=r'./agregadores/agregadores_' + name)

def gera_pwf_exporta_casos(SAVS, ANOS):
    ''' Cria pwf para exportar os CARTs dos savs '''
    pwfs = []
    with open(r'./agregadores/0. gera_pwfs_dos_savs.pwf', 'w') as f:
        for key, value in SAVS.items():
            f.write(f"ulog\n"
                    f"2\n"
                    f"{key}\n")
            for ano in ANOS:
                f.write(f"arqv rest\n"
                        f"{ano}\n"
                        f"ulog\n"
                        f"7\n"
                        f"../pwfs/{ano}_{value}.pwf\n"
                        f"cart\n"
                        f"(\n"
                        f"(\n")
                pwfs.append(f"./pwfs/{ano}_{value}.pwf")
        f.write('FIM')
    f.close()
    
    
    
    return (r'\agregadores\0. gera_pwfs_dos_savs.pwf', pwfs)

def gera_pwf_dados_agregadores():
    ''' Cria pwf de dados dos agregadores '''
    with open(r'.\agregadores\1. dados_agregadores.pwf', 'w') as f:
        f.write('dagr inic\n'
                'dagr\n'
                '001 Estado\n'
                ' 1    Acre\n'
                ' 2    Alagoas\n'
                ' 3    Amazonas\n'
                ' 4    Amapá\n'
                ' 5    Bahia\n'
                ' 6    Ceará\n'
                ' 7    Distrito Federal\n'
                ' 8    Espírito Santo\n'
                ' 9    Goiás\n'
                '10    Maranhão\n'
                '11    Minas Gerais\n'
                '12    Mato Grosso do Sul\n'
                '13    Mato Grosso\n'
                '14    Pará\n'
                '15    Paraíba\n'
                '16    Pernambuco\n'
                '17    Piauí\n'
                '18    Paraná\n'
                '19    Rio de Janeiro\n'
                '20    Rio Grande do Norte\n'
                '21    Rondônia\n'
                '22    Roraima\n'
                '23    Rio Grande do Sul\n'
                '24    Santa Catarina\n'
                '25    Sergipe\n'
                '26    São Paulo\n'
                '27    Tocantins\n'
                'fagr\n'
                '002 Estado_Para\n'
                ' 1    Acre\n'
                ' 2    Alagoas\n'
                ' 3    Amazonas\n'
                ' 4    Amapá\n'
                ' 5    Bahia\n'
                ' 6    Ceará\n'
                ' 7    Distrito Federal\n'
                ' 8    Espírito Santo\n'
                ' 9    Goiás\n'
                '10    Maranhão\n'
                '11    Minas Gerais\n'
                '12    Mato Grosso do Sul\n'
                '13    Mato Grosso\n'
                '14    Pará\n'
                '15    Paraíba\n'
                '16    Pernambuco\n'
                '17    Piauí\n'
                '18    Paraná\n'
                '19    Rio de Janeiro\n'
                '20    Rio Grande do Norte\n'
                '21    Rondônia\n'
                '22    Roraima\n'
                '23    Rio Grande do Sul\n'
                '24    Santa Catarina\n'
                '25    Sergipe\n'
                '26    São Paulo\n'
                '27    Tocantins\n'
                'fagr\n'
                '003 Região\n'
                '1     Norte\n'
                '2     Nordeste\n'
                '3     Centro Oeste\n'
                '4     Sudeste\n'
                '5     Sul\n'
                'fagr\n'
                '004 Tipo de Geração\n'
                '1     Compensador Estático\n'
                '2     Eólica\n'
                '3     Pequena Central Hidroelétrica\n'
                '4     Compensador Síncrono\n'
                '5     Usina Hidroelétrica\n'
                '6     Usina Nuclear\n'
                '7     Usina Termelétrica\n'
                '8     Usina Fotovoltáica\n'
                'fagr\n'
                '005 Classificação Instalação\n'
                ' 1    Rede Básica\n'
                ' 2    Rede de Fronteira\n'
                ' 3    Rede de Distribuição\n'
                ' 4    Rede de Uso Exclusivo\n'
                ' 5    Demais Instalações de Transmissão\n'
                '99999\n'
                'fim')
    f.close()
    return r'\agregadores\1. dados_agregadores.pwf.pwf'


def gera_pwf_salvar_agregadores(SAVS, ANOS):
    ''' Cria pwf para gravar dados dos agregadores nos casos '''
        
    with open(r'.\agregadores\2. salva_agregadores_nos_casos.pwf', 'w') as f:
        for key, value in SAVS.items():
            f.write(f"ulog\n"
                    f"2\n"
                    f"{key}\n")
            for ano in ANOS:
                f.write(f"arqv rest\n"
                        f"{ano}\n"
                        f"ulog\n"
                        f"1\n"
                        f"./1. dados_agregadores.pwf\n"
                        f"ulog\n"
                        f"1\n"
                        f"./agregadores_{ano}_{value}.pwf\n"
                        f"EXLF\n"
                        f"arqv grav subs novo\n"
                        f"{ano}\n"
                        f"(\n"
                        f"(\n")
        f.write('FIM')
    f.close()
    return r'\agregadores\2. salva_agregadores_nos_casos.pwf'



if __name__ == '__main__':   
    ## Entradas
    # diretorio do script
    SCRIPT_DIR = os.path.dirname(__file__)
    os.chdir(SCRIPT_DIR)
    
    ANAREDE_PATH = r"C:\Cepel\Anarede\V110400\ANAREDE.exe"
    
    ANOS = range(24, 34)
    
    SAVS = {
        # 'LNS.SAV':  'LNS',
        # 'LNU.SAV':  'LNU',
        # 'MNS.SAV':  'MNS',
        # 'MNU.SAV':  'MNU',
        # 'PNS.SAV':  'PNS',
        # 'PNU.SAV':  'PNU',
        'PES-PD 2029-NORTE UMIDO final.sav': 'PNU',
    }
    
    gera_pwf_dados_agregadores()
    
    subprocess.run([gera_pwf_exporta_casos(SAVS, ANOS), ANAREDE_PATH])

    FILES =  [f for f in os.listdir(r'./pwfs') if f[-4:] == '.PWF']
    
    gera_pwf_agregadores(FILES)
       
    subprocess.run([gera_pwf_salvar_agregadores(SAVS, ANOS), ANAREDE_PATH])
    
    subprocess.run([gera_pwf_exporta_casos(SAVS, ANOS), ANAREDE_PATH])
