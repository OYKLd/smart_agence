import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import json

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Administration - Smart Agence",
    page_icon="⚙️",
    layout="wide"
)

st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        background: linear-gradient(90deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_api_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API pour {endpoint}: {str(e)}")
        return []

def delete_agent(agent_id):
    try:
        response = requests.delete(f"{API_BASE_URL}/agents/{agent_id}")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def update_agent(agent_id, agent_data):
    try:
        response = requests.put(f"{API_BASE_URL}/agents/{agent_id}", json=agent_data)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_agent_statistics():
    agents = get_api_data("agents")
    tickets = get_api_data("tickets")
    stats = {
        'total_agents': len(agents),
        'agents_transaction': len([a for a in agents if a.get('categorie') == 'transaction']),
        'agents_conseil': len([a for a in agents if a.get('categorie') == 'conseil']),
        'total_tickets': len(tickets),
        'active_agents': len(set([t.get('agent_id') for t in tickets if t.get('agent_id')]))
    }
    return stats, agents, tickets

def export_data():
    agents = get_api_data("agents")
    tickets = get_api_data("tickets")
    return {
        'agents': agents,
        'tickets': tickets,
        'export_date': datetime.now().isoformat()
    }

def main():
    st.markdown("""
    <div class="admin-header">
        <h1>⚙️ Administration Smart Agence</h1>
        <p>Gestion avancée et maintenance du système</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Gestion Agents",
        "🎫 Gestion Tickets",
        "📊 Statistiques",
        "📁 Import/Export",
        "🔧 Maintenance"
    ])
    
    with tab1:
        show_agent_management()
    with tab2:
        show_ticket_management()
    with tab3:
        show_statistics()
    with tab4:
        show_import_export()
    with tab5:
        show_maintenance()

def show_agent_management():
    st.markdown('<div class="section-header"><h2>👥 Gestion Avancée des Agents</h2></div>', unsafe_allow_html=True)
    agents = get_api_data("agents")
    if not agents:
        st.warning("Aucun agent trouvé dans le système.")
        return
    st.subheader("📋 Liste des agents avec actions")
    df_agents = pd.DataFrame(agents)
    col1, col2, col3 = st.columns(3)
    with col1:
        if 'categorie' in df_agents.columns:
            categories = ['Toutes'] + list(df_agents['categorie'].unique())
            filter_category = st.selectbox("Filtrer par catégorie", categories)
    with col2:
        search_term = st.text_input("🔍 Rechercher un agent")
    with col3:
        sort_by = st.selectbox("Trier par", ['nom', 'prenoms', 'categorie', 'date_enregistrement'])
    filtered_df = df_agents.copy()
    if filter_category != 'Toutes':
        filtered_df = filtered_df[filtered_df['categorie'] == filter_category]
    if search_term:
        filtered_df = filtered_df[
            filtered_df['nom'].str.contains(search_term, case=False, na=False) |
            filtered_df['prenoms'].str.contains(search_term, case=False, na=False)
        ]
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by)
    for idx, agent in filtered_df.iterrows():
        with st.expander(f"👤 {agent.get('nom', '')} {agent.get('prenoms', '')} - {agent.get('categorie', '')}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                with st.form(f"edit_agent_{agent.get('agent_id')}"):
                    st.write("**Informations de l'agent:**")
                    new_nom = st.text_input("Nom", value=agent.get('nom', ''), key=f"nom_{agent.get('agent_id')}")
                    new_prenoms = st.text_input("Prénoms", value=agent.get('prenoms', ''), key=f"prenoms_{agent.get('agent_id')}")
                    new_email = st.text_input("Email", value=agent.get('email', ''), key=f"email_{agent.get('agent_id')}")
                    new_telephone = st.text_input("Téléphone", value=agent.get('telephone', ''), key=f"tel_{agent.get('agent_id')}")
                    new_categorie = st.selectbox(
                        "Catégorie",
                        ["transaction", "conseil"],
                        index=0 if agent.get('categorie') == 'transaction' else 1,
                        key=f"cat_{agent.get('agent_id')}"
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.form_submit_button("✏️ Modifier", type="primary"):
                            updated_data = {
                                "nom": new_nom,
                                "prenoms": new_prenoms,
                                "email": new_email,
                                "telephone": new_telephone,
                                "categorie": new_categorie,
                                "annee_naissance": agent.get('annee_naissance')
                            }
                            if update_agent(agent.get('agent_id'), updated_data):
                                st.success("✅ Agent modifié avec succès!")
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la modification")
                    with col_b:
                        if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                            if delete_agent(agent.get('agent_id')):
                                st.success("✅ Agent supprimé avec succès!")
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la suppression")
            with col2:
                st.write("**Statistiques:**")
                tickets = get_api_data("tickets")
                agent_tickets = [t for t in tickets if t.get('agent_id') == agent.get('agent_id')]
                st.metric("Tickets assignés", len(agent_tickets))
                if agent_tickets:
                    done_tickets = len([t for t in agent_tickets if t.get('statut') == 'done'])
                    st.metric("Tickets terminés", done_tickets)
                    st.metric("Taux de réussite", f"{(done_tickets/len(agent_tickets)*100):.1f}%")
                st.write(f"**ID:** {agent.get('agent_id')}")
                st.write(f"**Année naissance:** {agent.get('annee_naissance')}")
                st.write(f"**Date enregistrement:** {agent.get('date_enregistrement', 'N/A')[:10]}")

def show_ticket_management():
    st.markdown('<div class="section-header"><h2>🎫 Gestion Avancée des Tickets</h2></div>', unsafe_allow_html=True)
    tickets = get_api_data("tickets")
    agents = get_api_data("agents")
    if not tickets:
        st.warning("Aucun ticket trouvé dans le système.")
        return
    col1, col2, col3, col4 = st.columns(4)
    pending_count = len([t for t in tickets if t.get('statut') == 'pending'])
    progress_count = len([t for t in tickets if t.get('statut') == 'in_progress'])
    done_count = len([t for t in tickets if t.get('statut') == 'done'])
    canceled_count = len([t for t in tickets if t.get('statut') == 'canceled'])
    with col1:
        st.metric("⏳ En attente", pending_count)
    with col2:
        st.metric("🔄 En cours", progress_count)
    with col3:
        st.metric("✅ Terminés", done_count)
    with col4:
        st.metric("❌ Annulés", canceled_count)
    st.divider()
    st.subheader("🔍 Filtres avancés")
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Statut",
            ["Tous", "pending", "in_progress", "done", "canceled"]
        )
    with col2:
        if 'categorie_service' in pd.DataFrame(tickets).columns:
            categories = ["Toutes"] + list(set([t.get('categorie_service') for t in tickets if t.get('categorie_service')]))
            category_filter = st.selectbox("Catégorie de service", categories)
        else:
            category_filter = "Toutes"
    with col3:
        if 'priorite' in pd.DataFrame(tickets).columns:
            priorities = ["Toutes"] + list(set([t.get('priorite') for t in tickets if t.get('priorite')]))
            priority_filter = st.selectbox("Priorité", priorities)
        else:
            priority_filter = "Toutes"
    filtered_tickets = tickets.copy()
    if status_filter != "Tous":
        filtered_tickets = [t for t in filtered_tickets if t.get('statut') == status_filter]
    if category_filter != "Toutes":
        filtered_tickets = [t for t in filtered_tickets if t.get('categorie_service') == category_filter]
    if priority_filter != "Toutes":
        filtered_tickets = [t for t in filtered_tickets if t.get('priorite') == priority_filter]
    st.write(f"**{len(filtered_tickets)}** tickets correspondent aux critères")
    if filtered_tickets:
        for ticket in filtered_tickets[:20]:
            with st.expander(f"🎫 Ticket #{ticket.get('ticket_id')} - {ticket.get('categorie_service', 'N/A')} ({ticket.get('statut', 'N/A')})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {ticket.get('description', 'Aucune description')}")
                    st.write(f"**Statut:** {ticket.get('statut', 'N/A')}")
                    st.write(f"**Priorité:** {ticket.get('priorite', 'N/A')}")
                    st.write(f"**Catégorie:** {ticket.get('categorie_service', 'N/A')}")
                    agent_name = "Agent inconnu"
                    for agent in agents:
                        if agent.get('agent_id') == ticket.get('agent_id'):
                            agent_name = f"{agent.get('nom', '')} {agent.get('prenoms', '')}"
                            break
                    st.write(f"**Agent assigné:** {agent_name}")
                with col2:
                    st.write(f"**ID:** {ticket.get('ticket_id')}")
                    st.write(f"**Date création:** {ticket.get('date_creation', 'N/A')[:10] if ticket.get('date_creation') else 'N/A'}")
                    # Actions rapides (à implémenter selon API)
                    # if st.button(f"🚀 Passer en cours", key=f"progress_{ticket.get('ticket_id')}"):
                    #     st.success("Statut mis à jour!")
                    # if st.button(f"✅ Marquer terminé", key=f"done_{ticket.get('ticket_id')}"):
                    #     st.success("Ticket terminé!")

def show_statistics():
    st.markdown('<div class="section-header"><h2>📊 Statistiques Avancées</h2></div>', unsafe_allow_html=True)
    stats, agents, tickets = get_agent_statistics()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total agents", stats['total_agents'])
    with col2:
        st.metric("🎫 Total tickets", stats['total_tickets'])
    with col3:
        st.metric("🟢 Agents actifs", stats['active_agents'])
    st.divider()
    df_agents = pd.DataFrame(agents)
    if not df_agents.empty and 'categorie' in df_agents.columns:
        fig = px.pie(df_agents, names='categorie', title="Répartition des agents par catégorie")
        st.plotly_chart(fig, use_container_width=True)
    df_tickets = pd.DataFrame(tickets)
    if (
        not df_tickets.empty and
        not df_agents.empty and
        'agent_id' in df_tickets.columns and
        'agent_id' in df_agents.columns
    ):
        ticket_counts = df_tickets.groupby('agent_id').size().reset_index(name='nb_tickets')
        merged = pd.merge(ticket_counts, df_agents, left_on='agent_id', right_on='agent_id', how='left')
        merged['nom_complet'] = merged['nom'].fillna('') + " " + merged['prenoms'].fillna('')
        fig2 = px.bar(merged, x='nom_complet', y='nb_tickets', title="Tickets par agent", color='nb_tickets')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Impossible d'afficher la répartition des tickets par agent (données manquantes).")
    if not df_tickets.empty and 'date_creation' in df_tickets.columns:
        df_tickets['date_creation'] = pd.to_datetime(df_tickets['date_creation'])
        df_tickets['jour'] = df_tickets['date_creation'].dt.date
        daily_counts = df_tickets.groupby('jour').size().reset_index(name='nb_tickets')
        fig3 = px.line(daily_counts, x='jour', y='nb_tickets', title="Évolution quotidienne des tickets")
        st.plotly_chart(fig3, use_container_width=True)

def show_import_export():
    st.markdown('<div class="section-header"><h2>📁 Import / Export</h2></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📤 Exporter les données")
        if st.button("Télécharger les données JSON"):
            data = export_data()
            json_str = json.dumps(data, indent=4)
            st.download_button(
                label="📥 Télécharger",
                data=json_str,
                file_name=f"export_smart_agence_{date.today()}.json",
                mime="application/json"
            )
    with col2:
        st.subheader("📥 Importer les données (non implémenté)")
        st.info("💡 La fonctionnalité d'import est prévue mais non disponible pour le moment.")

def show_maintenance():
    st.markdown('<div class="section-header"><h2>🔧 Maintenance et sécurité</h2></div>', unsafe_allow_html=True)
    with st.expander("🧹 Réinitialiser la base de données"):
        st.warning("⚠️ Attention, cette action supprimera toutes les données actuelles.")
        if st.button("❌ Réinitialiser", type="secondary"):
            try:
                response = requests.post(f"{API_BASE_URL}/reset")
                if response.status_code == 200:
                    st.success("✅ Base de données réinitialisée avec succès.")
                    st.rerun()
                else:
                    st.error("❌ Échec de la réinitialisation.")
            except Exception as e:
                st.error(f"Erreur : {e}")
    with st.expander("🛠️ Diagnostique système"):
        st.write("📡 Connexion API :", "🟢 OK" if get_api_data("agents") else "🔴 Problème")
        st.write("📦 Version pandas :", f"{pd.__version__}")
        st.write("📈 Nombre total de tickets :", len(get_api_data("tickets")))

if __name__ == "__main__":
    main()