import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(
    page_title="Smart Agence - Gestion de Clients",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"

st.markdown("""
<style>
    .main-header {
        font-size: 3rem !important;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def get_agents():
    try:
        response = requests.get(f"{API_BASE_URL}/agents/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        st.error("Impossible de se connecter à l'API")
        return []

def get_tickets():
    try:
        response = requests.get(f"{API_BASE_URL}/tickets/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        st.error("Impossible de se connecter à l'API")
        return []

def create_agent(agent_data):
    try:
        response = requests.post(f"{API_BASE_URL}/agents/", json=agent_data)
        if response.status_code not in (200, 201):
            st.error(f"Erreur API: {response.status_code} - {response.text}")
        return response.status_code in (200, 201)
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return False

def create_ticket(ticket_data):
    try:
        response = requests.post(f"{API_BASE_URL}/tickets/", json=ticket_data)
        if response.status_code != 201:
            st.error(f"Erreur API: {response.status_code} - {response.text}")
        return response.status_code == 201
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return False

def update_ticket_status(ticket_id, status_data):
    try:
        response = requests.post(f"{API_BASE_URL}/tickets/{ticket_id}/status", json=status_data)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def main():
    st.markdown('<h1 class="main-header">🏢 Smart Agence</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #7f8c8d; font-size: 1.2rem;">Système de gestion de clients et tickets</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.selectbox(
            "Choisir une section",
            ["🏠 Tableau de bord", "👥 Gestion des agents", "🎫 Gestion des tickets"],
            index=0
        )
    
    if page == "🏠 Tableau de bord":
        show_dashboard()
    elif page == "👥 Gestion des agents":
        show_agents_management()
    elif page == "🎫 Gestion des tickets":
        show_tickets_management()

def show_dashboard():
    """Affiche le tableau de bord avec les statistiques"""
    st.header("📊 Tableau de bord")
    
    # Récupération des données
    agents = get_agents()
    tickets = get_tickets()
    
    if not agents and not tickets:
        st.warning("Aucune donnée disponible. Vérifiez que l'API est démarrée.")
        return
    
    # Métriques principales en colonnes
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👥 Agents totaux",
            value=len(agents),
            delta=f"+{len([a for a in agents if 'date_enregistrement' in a])}"
        )
    
    with col2:
        total_tickets = len(tickets)
        st.metric(
            label="🎫 Tickets totaux",
            value=total_tickets,
            delta=f"+{len([t for t in tickets if t.get('statut') == 'pending'])}"
        )
    
    with col3:
        done_tickets = len([t for t in tickets if t.get('statut') == 'done'])
        st.metric(
            label="✅ Tickets traités",
            value=done_tickets,
            delta=f"{(done_tickets/total_tickets*100):.1f}%" if total_tickets > 0 else "0%"
        )
    
    with col4:
        pending_tickets = len([t for t in tickets if t.get('statut') == 'pending'])
        st.metric(
            label="⏳ En attente",
            value=pending_tickets,
            delta=f"-{len([t for t in tickets if t.get('statut') == 'in_progress'])}"
        )
    
    st.divider()
    
    # Graphiques
    if tickets:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Répartition des tickets par statut")
            
            # Données pour le graphique en secteurs
            status_counts = {}
            for ticket in tickets:
                status = ticket.get('statut', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                fig_pie = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    color_discrete_map={
                        'pending': '#ffd700',
                        'in_progress': '#1f77b4',
                        'done': '#2ca02c',
                        'canceled': '#d62728'
                    }
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("👥 Tickets par agent")
            
            # Données pour le graphique en barres
            agent_tickets = {}
            for ticket in tickets:
                agent_id = ticket.get('agent_id', 'Non assigné')
                agent_name = "Agent inconnu"
                
                # Trouver le nom de l'agent
                for agent in agents:
                    if agent.get('agent_id') == agent_id:
                        agent_name = f"{agent.get('nom', '')} {agent.get('prenoms', '')}"
                        break
                
                agent_tickets[agent_name] = agent_tickets.get(agent_name, 0) + 1
            
            if agent_tickets:
                fig_bar = px.bar(
                    x=list(agent_tickets.keys()),
                    y=list(agent_tickets.values()),
                    color=list(agent_tickets.values()),
                    color_continuous_scale='viridis'
                )
                fig_bar.update_layout(
                    xaxis_title="Agents",
                    yaxis_title="Nombre de tickets",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Graphique des catégories de service
        st.subheader("🏷️ Tickets par catégorie de service")
        
        category_counts = {}
        for ticket in tickets:
            category = ticket.get('categorie_service', 'Non définie')
            category_counts[category] = category_counts.get(category, 0) + 1
        
            if category_counts:
                fig_category = px.bar(
                    x=list(category_counts.keys()),
                    y=list(category_counts.values()),
                    color=list(category_counts.values()),
                    color_continuous_scale='plasma'
                )
                fig_category.update_layout(
                    xaxis_title="Catégorie de service",
                    yaxis_title="Nombre de tickets",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_category, use_container_width=True)

def show_agents_management():
    """Affiche la gestion des agents"""
    st.header("👥 Gestion des agents")
    
    tab1, tab2 = st.tabs(["➕ Ajouter un agent", "📋 Liste des agents"])
    
    with tab1:
        st.subheader("Enregistrer un nouvel agent")
        
        with st.form("agent_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom *", placeholder="Koffi")
                prenoms = st.text_input("Prénoms *", placeholder="Paul")
                email = st.text_input("Email", placeholder="paul.koffi@gmail.com")
            
            with col2:
                annee_naissance = st.number_input(
                    "Année de naissance *",
                    min_value=1950,
                    max_value=datetime.now().year - 18,
                    value=1990
                )
                categorie = st.selectbox(
                    "Catégorie *",
                    ["transaction", "conseil"]
                )
                telephone = st.text_input("Téléphone", placeholder="+225 00 00 00 00 00")
            
            submitted = st.form_submit_button("🚀 Enregistrer l'agent", type="primary")
            
            if submitted:
                if nom and prenoms and annee_naissance and categorie:
                    agent_data = {
                        "nom": nom,
                        "prenoms": prenoms,
                        "annee_naissance": annee_naissance,
                        "categorie": categorie,
                        "email": email if email else None,
                        "telephone": telephone if telephone else None,
                        "date_enregistrement": datetime.now().isoformat()
                    }
                    
                    if create_agent(agent_data):
                        st.success("✅ Agent enregistré avec succès!")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de l'enregistrement de l'agent")
                else:
                    st.error("⚠️ Veuillez remplir tous les champs obligatoires (*)")
    
    with tab2:
        st.subheader("Liste des agents enregistrés")
        
        agents = get_agents()
        
        if agents:
            # Conversion en DataFrame pour un meilleur affichage
            df_agents = pd.DataFrame(agents)
            
            # Filtres
            col1, col2 = st.columns(2)
            with col1:
                if 'categorie' in df_agents.columns:
                    categories = ['Toutes'] + list(df_agents['categorie'].unique())
                    filter_category = st.selectbox("Filtrer par catégorie", categories)
            
            with col2:
                search_term = st.text_input("🔍 Rechercher par nom", placeholder="Tapez un nom...")
            
            # Application des filtres
            filtered_df = df_agents.copy()
            
            if filter_category != 'Toutes':
                filtered_df = filtered_df[filtered_df['categorie'] == filter_category]
            
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['nom'].str.contains(search_term, case=False, na=False) |
                    filtered_df['prenoms'].str.contains(search_term, case=False, na=False)
                ]
            
            # Affichage du tableau
            st.dataframe(
                filtered_df,
                use_container_width=True,
                column_config={
                    "agent_id": "ID",
                    "nom": "Nom",
                    "prenoms": "Prénoms",
                    "annee_naissance": "Année naissance",
                    "categorie": "Catégorie",
                    "email": "Email",
                    "telephone": "Téléphone",
                    "date_enregistrement": "Date d'enregistrement"
                }
            )
            
            st.info(f"📊 Total: {len(filtered_df)} agent(s) affiché(s)")
        else:
            st.info("Aucun agent enregistré pour le moment.")

def show_tickets_management():
    """Affiche la gestion des tickets"""
    st.header("🎫 Gestion des tickets")
    
    tab1, tab2, tab3 = st.tabs(["➕ Nouveau ticket", "📋 Liste des tickets", "🔄 Changer statut"])
    
    with tab1:
        st.subheader("Créer un nouveau ticket")
        
        agents = get_agents()
        for a in agents:
            if 'agent_id' not in a and 'id' in a:
                a['agent_id'] = a['id']
        agents = [a for a in agents if 'agent_id' in a]
        if not agents:
            st.warning("⚠️ Aucun agent disponible. Veuillez d'abord enregistrer des agents.")
            return
        
        with st.form("ticket_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélection de l'agent
                agent_options = {f"{a['nom']} {a['prenoms']} ({a['categorie']})": a['agent_id'] for a in agents}
                selected_agent_display = st.selectbox("Agent assigné *", list(agent_options.keys()))
                selected_agent_id = agent_options[selected_agent_display]
                
                categorie_service = st.selectbox(
                    "Catégorie de service *",
                    ["Consultation", "Transaction", "Support", "Réclamation", "Information"]
                )
            
            with col2:
                description = st.text_area(
                    "Description du ticket",
                    placeholder="Décrivez la demande du client...",
                    height=100
                )
                
                priorite = st.selectbox("Priorité", ["Basse", "Normale", "Haute", "Urgente"])
            
            submitted = st.form_submit_button("🎫 Créer le ticket", type="primary")
            
            if submitted:
                ticket_data = {
                    "agent_id": selected_agent_id,
                    "categorie_service": categorie_service,
                    "description": description if description else None,
                    "priorite": priorite,
                    "date_creation": datetime.now().isoformat(),
                    "statut": "pending"
                }
                
                if create_ticket(ticket_data):
                    st.success("✅ Ticket créé avec succès!")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la création du ticket")
    
    with tab2:
        st.subheader("Liste des tickets")
        
        tickets = get_tickets()
        agents = get_agents()
        
        if tickets:
            # Enrichissement des données avec les noms des agents
            enriched_tickets = []
            for ticket in tickets:
                enriched_ticket = ticket.copy()
                agent_name = "Agent inconnu"
                for agent in agents:
                    if agent.get('agent_id') == ticket.get('agent_id'):
                        agent_name = f"{agent.get('nom', '')} {agent.get('prenoms', '')}"
                        break
                enriched_ticket['agent_name'] = agent_name
                enriched_tickets.append(enriched_ticket)
            
            df_tickets = pd.DataFrame(enriched_tickets)
            
            # Filtres
            col1, col2, col3 = st.columns(3)

            filter_status = 'Tous'
            filter_service = 'Toutes'
            filter_agent = 'Tous'

            with col1:
                if 'statut' in df_tickets.columns:
                    statuts = ['Tous'] + list(df_tickets['statut'].unique())
                    filter_status = st.selectbox("Filtrer par statut", statuts)

            with col2:
                if 'categorie_service' in df_tickets.columns:
                    categories = ['Toutes'] + list(df_tickets['categorie_service'].unique())
                    filter_service = st.selectbox("Filtrer par service", categories)

            with col3:
                if 'agent_name' in df_tickets.columns:
                    agents_list = ['Tous'] + list(df_tickets['agent_name'].unique())
                    filter_agent = st.selectbox("Filtrer par agent", agents_list)

            # Application des filtres
            filtered_df = df_tickets.copy()

            if filter_status != 'Tous':
                filtered_df = filtered_df[filtered_df['statut'] == filter_status]

            if filter_service != 'Toutes':
                filtered_df = filtered_df[filtered_df['categorie_service'] == filter_service]

            if filter_agent != 'Tous':
                filtered_df = filtered_df[filtered_df['agent_name'] == filter_agent]
            
            # Affichage du tableau avec style conditionnel
            def color_status(val):
                color_map = {
                    'pending': 'background-color: #fff3cd',
                    'in_progress': 'background-color: #cce5ff',
                    'done': 'background-color: #d4edda',
                    'canceled': 'background-color: #f8d7da'
                }
                return color_map.get(val, '')
            
            styled_df = filtered_df.style.applymap(color_status, subset=['statut'] if 'statut' in filtered_df.columns else [])
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                column_config={
                    "ticket_id": "ID Ticket",
                    "agent_name": "Agent assigné",
                    "categorie_service": "Service",
                    "statut": "Statut",
                    "priorite": "Priorité",
                    "date_creation": "Date création",
                    "description": "Description"
                }
            )
            
            st.info(f"📊 Total: {len(filtered_df)} ticket(s) affiché(s)")
        else:
            st.info("Aucun ticket créé pour le moment.")
    
    with tab3:
        st.subheader("Changer le statut d'un ticket")
        
        tickets = get_tickets()
        
        if tickets:
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélection du ticket
                ticket_options = {
                    f"Ticket #{t.get('ticket_id')} - {t.get('categorie_service', 'N/A')} ({t.get('statut', 'N/A')})": t.get('ticket_id')
                    for t in tickets
                }
                
                selected_ticket_display = st.selectbox("Sélectionner un ticket", list(ticket_options.keys()))
                selected_ticket_id = ticket_options[selected_ticket_display]
                
                # Trouver le ticket sélectionné pour afficher les détails
                selected_ticket = next((t for t in tickets if t.get('ticket_id') == selected_ticket_id), None)
                
                if selected_ticket:
                    st.info(f"**Statut actuel:** {selected_ticket.get('statut', 'N/A')}")
            
            with col2:
                new_status = st.selectbox(
                    "Nouveau statut",
                    ["pending", "in_progress", "done", "canceled"],
                    help="Choisissez le nouveau statut pour le ticket"
                )
                
                commentaire = st.text_area("Commentaire (optionnel)", placeholder="Raison du changement de statut...")
            
            if st.button("🔄 Mettre à jour le statut", type="primary"):
                status_data = {
                    "statut": new_status,
                    "commentaire": commentaire if commentaire else None,
                    "date_modification": datetime.now().isoformat()
                }
                
                if update_ticket_status(selected_ticket_id, status_data):
                    st.success(f"✅ Statut du ticket #{selected_ticket_id} mis à jour vers '{new_status}'!")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la mise à jour du statut")
        else:
            st.info("Aucun ticket disponible pour modification.")

if __name__ == "__main__":
    main()