# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import yfinance as yf #0.1.54
import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
from pandas_datareader import data as pdr


import plotly_express as px

st.set_page_config(page_title="Optimisation d'un portefeuille d'ETF ",page_icon="🎯",layout="wide",initial_sidebar_state="expanded")

st.markdown("<h1 style='text-align: center; color: Navy;'>Optimisation à visée éducative d'un portefeuille d'ETF </h1>", unsafe_allow_html=True)




def init(etfs):
  """
  return la date maximale de prise en compte des calculs (date la plus récente)
  """
  hist_list=[]
  for i in range(len(etfs)):
    etfi=yf.Ticker(etfs[i])
    hist_list.append(etfi.history(period="max")['Close'])
    date_i=hist_list[i].index[0]
    if i==0:
      max_date=date_i
    elif date_i>max_date:
      max_date=date_i
  
  return max_date

def init_max_date(etfs):
  """
  return la liste des ETF avec la même date de prise en compte (la plus récente)
  """
  max_date=init(etfs)


  ####
  yf.pdr_override()
  price_data = pdr.get_data_yahoo(etfs, start=max_date)['Adj Close']
  if len(etfs)==1:
      price_data=price_data.to_frame()
      price_data.columns=[etfs[0]]

  return price_data


def init_var(num_port, price_data):
  # Simulating 5000 portfolios
  num_port = 3000
  # Creating an empty array to store portfolio weights
  all_wts = np.zeros((num_port, len(price_data.columns)))
  # Creating an empty array to store portfolio returns
  port_returns = np.zeros((num_port))
  # Creating an empty array to store portfolio risks
  port_risk = np.zeros((num_port))
  # Creating an empty array to store portfolio sharpe ratio
  sharpe_ratio = np.zeros((num_port))

  log_ret = np.log(price_data/price_data.shift(1))

  cov_mat = log_ret.cov() * 252
  return num_port, all_wts, port_returns, port_risk, sharpe_ratio, log_ret, cov_mat


def simulation(num_port, price_data):
    num_port, all_wts, port_returns, port_risk, sharpe_ratio, log_ret, cov_mat=init_var(num_port, price_data)

    for i in range(num_port):
      wts = np.random.uniform(size = len(price_data.columns))
      wts = wts/np.sum(wts)
      # saving weights in the array
      all_wts[i,:] = wts
      # Portfolio Returns
      port_ret = np.sum(log_ret.mean() * wts)
      port_ret = (port_ret + 1) ** 252 - 1
      # Saving Portfolio returns
      port_returns[i] = port_ret
      # Portfolio Risk
      port_sd = np.sqrt(np.dot(wts.T, np.dot(cov_mat, wts)))
      port_risk[i] = port_sd
      # Portfolio Sharpe Ratio
      # Assuming 0% Risk Free Rate
      sr = port_ret / port_sd
      sharpe_ratio[i] = sr


    min_var = all_wts[port_risk.argmin()]
    max_sr = all_wts[sharpe_ratio.argmax()]
    min_var = [pd.DataFrame(min_var, index = price_data.columns, columns = ['Portfolio weights']), port_returns[port_risk.argmin()],port_risk[port_risk.argmin()]]
    max_sr = [pd.DataFrame(max_sr, index = price_data.columns, columns = ['Portfolio weights']), port_returns[sharpe_ratio.argmax()],port_risk[sharpe_ratio.argmax()]]
    return min_var, max_sr, port_returns,port_risk
    

def allocation_display(price_data,weight):
    names = price_data.columns
    df = pd.Series(weight['Portfolio weights'].values, index=names)
      
    fig = px.pie(values=df.values, names=df.index,width=400, height =400)
    st.write(fig)


def evolution_port_display(duree_future,perf,invest_init, invest_mens):
  """
  calcule l'evolution du capital depuis l'apparition du dernier ETF (ou 10 ans) jusqu'a 2021 + duree future.
  """
  
  interet=[invest_init+12*invest_mens]
  apport=[invest_init+12*invest_mens]
  date_now=datetime.now().year
  for i in range(duree_future):
    if i==0:
      interet[i]=round(interet[i]*(1+perf))
      annee=[date_now]
    else :
      ajout=12*invest_mens+interet[i-1]
      apport.append(12*invest_mens+apport[i-1])
      val_port=round(ajout*(1+perf))
      interet.append(val_port)
      annee.append(annee[-1]+1)

  interet_cum=list(np.array(interet)-np.array(apport))
  port = pd.DataFrame(columns=['an','apport','interet'])
  port['apport']=apport
  port['interet']=interet_cum
  port['an']=annee
  
  

  port2 = pd.DataFrame(columns=['An','Capital','Composition Portefeuille'])
  k=0
  for i in range(port.shape[0]):
      val_interet=port['interet'][i]
      val_apport=port['apport'][i]
      annee=port['an'][i]
      port2.loc[k,:]=annee,val_apport,'Investissement initial + mensuel'
      port2.loc[k+1,:]=annee,val_interet,'Interets cumulés'
      
      k=k+2

  fig = px.bar(port2, x="An", y="Capital", color="Composition Portefeuille", title="",width=500, height =500)
  fig.update_layout(legend=dict(yanchor="top",y=0.99, xanchor="left", x=0.01))
  st.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Evolution du capital investi</h2>", unsafe_allow_html=True)
  st.write(fig)
  
  annee_display = port['an'].values[-1]
  val_capital=port['apport'].values[-1]+port['interet'].values[-1]
  st.markdown("<h3 style='text-align: center; color: LimeGreen;'> En {} : Capital total estimé de {} euros !</h3>".format(annee_display, val_capital), unsafe_allow_html=True)

    




def planning(price_data,etfs,weight):
  mois=['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre','Novembre', 'Décembre']
  month_now=datetime.now().month
  annee1=str(datetime.now().year)
  annee2=str(datetime.now().year+1)
  a=mois[month_now-1:]
  b=mois[:month_now-1]
  for i in range(len(a)):
    a[i]=a[i] +' ' + annee1
  for i in range(len(b)):
    b[i]=b[i] +' ' + annee2

  mois_2=a+b
  col=[]
  price_unique=pd.DataFrame(price_data.iloc[-1,:].values, index = etfs, columns = ['price'])
  #print(weight['Portfolio weights'])
  price_unique['invest_12mois']=weight['Portfolio weights']*(invest_init+12*invest_mens)
  price_unique['invest_mens']=price_unique['invest_12mois']/12
  price_unique['capital_disponible']=price_unique['invest_12mois']/12
  #print(price_unique,1)
  for i in range(1,13):
    price_unique['mois_{}'.format(i)]=[0]*len(price_data.iloc[-1,:].values)
    col.append('mois_{}'.format(i))
  price_unique['mois_1']=np.floor(price_unique['capital_disponible']/price_unique['price'])
  #print(price_unique,2)
  prix_etf=price_unique['price'].values
  for i in range(1,12):
    price_unique['capital_disponible']= price_unique['invest_mens'] + price_unique['capital_disponible']-price_unique['mois_{}'.format(i)]*price_unique['price']
    price_unique['mois_{}'.format(i+1)]=np.floor(price_unique['capital_disponible']/price_unique['price'])
  #print(price_unique,3)
  price_unique['capital_disponible']= price_unique['capital_disponible']-price_unique['mois_12']*price_unique['price']
  price_unique=price_unique[col]
  price_unique=price_unique.T
  price_unique.columns=["Nb {}".format(k) for k in price_unique.columns]
  price_unique.index=mois_2
  price_unique.loc["Nb ETF/an"]=[price_unique[col].sum() for col in price_unique.columns]
  price_unique.loc['prix_etf']=prix_etf
  price_unique.loc["ETF €/an"]=round(price_unique.loc['prix_etf']*price_unique.loc["Nb ETF/an"])
  price_unique=price_unique.drop('prix_etf')
  price_unique=price_unique.astype('int32')
  
  st.dataframe(price_unique)



def top_perf_utilisateur(max_sr_perf,max_sr_risk):
  sharpe= max_sr_perf/max_sr_risk
  if 0<=sharpe<0.1 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 5% des stratégies les moins performantes essayées sur cette plateforme.  ")
  elif 0.1<=sharpe<0.2 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 15% des stratégies les moins performantes essayées sur cette plateforme.  ")
  elif 0.2<=sharpe<0.3 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 25% des stratégies les moins performantes essayées sur cette plateforme.  ")
  elif 0.3<=sharpe<0.4 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 35% des stratégies les moins performantes essayées sur cette plateforme.  ")
  elif 0.4<=sharpe<0.5 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 45% des stratégies les plus performantes essayées sur cette plateforme.  ")
  elif 0.5<=sharpe<0.6 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 35% des stratégies les plus performantes essayées sur cette plateforme.  ")
  elif 0.6<=sharpe<0.7 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 25% des stratégies les plus performantes essayées sur cette plateforme.  ")
  elif 0.7<=sharpe<0.8 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 15% des stratégies les plus performantes essayées sur cette plateforme.  ")
  elif 0.8<=sharpe<0.9 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 8% des stratégies les plus performantes essayées sur cette plateforme.  ")
  elif 1<=sharpe<1.2 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 5% des stratégies les plus performantes essayées sur cette plateforme.  ")
  elif 1.2<=sharpe<1.5 :
    st.write("L'allocation de portefeuille optimisée avec les ETF que vous avez rentré fait partie des 2% des stratégies les plus performantes essayées sur cette plateforme.  ")
  else :
    pass



@st.cache
def data_load():
    path="etf_liste.csv"
    path2 = "/home/pierrelouis/Bureau/etf/etf_liste.csv"
    etf_data = pd.read_csv(path)
    return(etf_data)
    
def filtre(etf_data):
    col=['FISCAL','REGIONS','STRATEGIES']
    my_expander = st.beta_expander(label='Clique ici pour filtrer tes ETF')
    with my_expander:
        fiscal=st.selectbox("Enveloppe fiscale : ",options=['TOUT']+list(etf_data[col[0]].unique()) )
        regions=st.selectbox("Regions du monde : ",options=['TOUT']+list(etf_data[col[1]].unique()))
        strategies=st.selectbox("Stratégies d'investissement :",options=['TOUT']+list(etf_data[col[2]].unique()) )
    filtre=[fiscal, regions, strategies]
    
    etf_data_filtre=etf_data
    for i in range(len(filtre)) :
        if filtre[i] != 'TOUT':
            name=col[i]
            etf_data_filtre=etf_data_filtre[etf_data_filtre[name]==filtre[i]]
            
    st.dataframe(etf_data_filtre)
    
    
def portefeuille(etf_data):
    st.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Selection de ton portefeuille</h2>", unsafe_allow_html=True)
    st.write("Indique ci-dessous les numéros des ETF pris en compte pour l'optimisation (cf screener ci-dessus) : ")
    indice = st.multiselect(' ', list(etf_data['NUMERO_ETF']))
    etf_port_indice = etf_data.loc[indice]
    st.write(' ')
    st.write("Ton portefeuille actuel :")
    st.write(etf_port_indice)
    return(indice)
    
    
def ticker(indice, etf_data):
    ticker=[]
    for i in indice:
        ticker.append(etf_data[etf_data['NUMERO_ETF'] == i]['TICKER'].values.tolist()[0]+'.PA')

    return(ticker)


def initialisation():
    st.sidebar.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Personnalisation</h2>", unsafe_allow_html=True)
    st.sidebar.subheader('Investissement initial: €')
    invest_init = st.sidebar.number_input("",min_value=0, max_value=1000000, step=100, value=1000,key='init')
    st.sidebar.subheader('Investissement mensuel : €')
    invest_mens= st.sidebar.number_input("", min_value=0, max_value=1000000, step=100, value=300,key='mens')
    st.sidebar.subheader("Durée de l'investissement : ans")
    duree= st.sidebar.number_input("", min_value=0, max_value=70, step=1, value=5,key='duree')
    st.sidebar.subheader("Stratégie souhaitée ?")
    strategie = st.sidebar.radio("", options=['Maximisation de la performance','Minimisation du risque'])
    if strategie == 'Minimisation du risque':
        strategie = 'risque'
    else :
        strategie="perf"
        
    formulaire()
        
    return(duree, invest_init, invest_mens,strategie)


def launch_compute():
    duree, invest_init, invest_mens, strategie=initialisation()
    etf_data=data_load()
    filtre(etf_data)
    indice=portefeuille(etf_data)
    bouton_calcule=st.button("Démarrer l'optimisation de ton portefeuille")
    return(duree,invest_init, invest_mens, indice, bouton_calcule,strategie,etf_data)
    
def formulaire():
    st.sidebar.subheader("Restons en contact")
    html='<iframe src="https://docs.google.com/forms/d/e/1FAIpQLSfzR9YfAJ1bsDZWq0Tw9jme20UFeUoiFfZ8OnoePwGpmLGeLg/viewform?embedded=true" width="300" height="300" frameborder="0" marginheight="0" marginwidth="0">Chargement…</iframe>'
    st.sidebar.markdown(html, unsafe_allow_html=True)


    


if __name__ == "__main__":
    


    
    col1, col_vide,col2, col_vide2,col3 = st.beta_columns([0.8,0.05,1,0.05,1])
    
    ############# 1ere page terminee #############################
    with col1:
        st.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Screener d'ETF (1)</h2>", unsafe_allow_html=True)
        duree,invest_init, invest_mens, indice, bouton_calcule,strategie,etf_data=launch_compute()
    ############ 1ere page terminee #############################
    

    #st.write('Hello, *World!* :sunglasses:')
        

    if bouton_calcule==True:
        #col1, col_vide,col2, col_vide2,col3 = st.beta_columns([2,0.05,1,0.05,1])

    
        ticker_list=ticker(indice, etf_data)
        price_data=init_max_date(ticker_list)
        
        min_var,max_sr,port_returns,port_risk=simulation(10, price_data)
        if strategie == 'risque':
            weigth, perf, risk=min_var[0],min_var[1],min_var[2]
            perf=np.exp(perf)-1
        else :
            weigth, perf, risk=max_sr[0],max_sr[1],max_sr[2]
            perf=np.exp(perf)-1
        
        with col2:
            st.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Allocation optimisée (2)</h2>", unsafe_allow_html=True)
            st.write("Voici l'allocation optimisée du portefeuille avec les paramètres fournis :")
            allocation_display(price_data,weigth)
            st.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Planning d'investissement sur 1 an</h2>", unsafe_allow_html=True)
            planning(price_data,ticker_list,weigth)
    
        with col3 :
            st.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Evaluation de cette stratégie (3)</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: Black;'>La performance annualisée du portefeuille optimisé est de :</h4>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: LimeGreen;'>{} % !</h3>".format(round(perf*100,2)), unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: Black;'>La volatilité annualisée du portefeuille optimisé est de :</h4>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: LimeGreen;'>{} % !</h3>".format(round(risk*100, 2)), unsafe_allow_html=True)
            evolution_port_display(duree,perf,invest_init,invest_mens)
            #top_perf_utilisateur(perf,risk)
            #st.markdown("<h2 style='text-align: center; color: RoyalBlue;'>Ebook ETF</h2>", unsafe_allow_html=True)

            






