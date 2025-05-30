import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Dashboard - Smart Agence",
    page_icon="📊",
    layout="wide"
)

# Styles CSS
st.markdown("""
<style>
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
    }
    .metric-delta {
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .dashboard-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_api_data(endpoint):
    """Fonction générique pour récupérer des données de l'API"""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        st.error(f"Erreur de connexion à l'API pour {endpoint}")
        return []

def calculate_metrics(agents, tickets):
    """Calcule les métriques pour le dashboard"""
    metrics = {
        'total_agents': len(agents),
        'total_tickets': len(tickets),
        'pending_tickets': len([t for t in tickets if t.get('statut') == 'pending']),
        'in_progress_tickets': len([t for t in tickets if t.get('statut') == 'in_progress']),
        'done_tickets': len([t for t in tickets if t.get('statut') == 'done']),
        'canceled_tickets': len([t for t in tickets if t.get('statut') == 'canceled']),
    }
    
    # Calculs supplémentaires
    if metrics['total_tickets'] > 0:
        metrics['completion_rate'] = (metrics['done_tickets'] / metrics['total_tickets']) * 100
        metrics['pending_rate'] = (metrics['pending_tickets'] / metrics['total_tickets']) * 100
    else:
        metrics['completion_rate'] = 0
        metrics['pending_rate'] = 0
    
    # Agents par catégorie
    metrics['agents_transaction'] = len([a for a in agents if a.get('categorie') == 'transaction'])
    metrics['agents_conseil'] = len([a for a in agents if a.get('categorie') == 'conseil'])
    
    return metrics

def create_status_distribution_chart(tickets):
    """Crée un graphique de distribution des statuts"""
    status_counts = {}
    status_labels = {
        'pending': 'En attente',
        'in_progress': 'En cours',
        'done': 'Terminé',
        'canceled': 'Annulé'
    }
    
    for ticket in tickets:
        status = ticket.get('statut', 'unknown')
        display_status = status_labels.get(status, status)
        status_counts[display_status] = status_counts.get(display_status, 0) + 1
    
    if not status_counts:
        return None
    
    colors = ['#ffd700', '#1f77b4', '#2ca02c', '#d62728']
    
    fig = go.Figure(data=[go.Pie(
        labels=list(status_counts.keys()),
        values=list(status_counts.values()),
        hole=0.4,
        marker=dict(colors=colors[:len(status_counts)]),
        textinfo='label+percent+value',
        textposition='outside'
    )])
    
    fig.update_layout(
        title={
            'text': "Répartition des tickets par statut",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

def create_agent_performance_chart(agents, tickets):
    """Crée un graphique de performance des agents"""
    agent_performance = {}
    
    for agent in agents:
        agent_id = agent.get('agent_id')
        agent_name = f"{agent.get('nom', '')[:10]} {agent.get('prenoms', '')[:1]}."
        agent_tickets = [t for t in tickets if t.get('agent_id') == agent_id]
        
        agent_performance[agent_name] = {
            'total': len(agent_tickets),
            'done': len([t for t in agent_tickets if t.get('statut') == 'done']),
            'pending': len([t for t in agent_tickets if t.get('statut') == 'pending']),
            'in_progress': len([t for t in agent_tickets if t.get('statut') == 'in_progress'])
        }
    
    if not agent_performance:
        return None
    
    agents_names = list(agent_performance.keys())
    done_counts = [agent_performance[name]['done'] for name in agents_names]
    pending_counts = [agent_performance[name]['pending'] for name in agents_names]
    in_progress_counts = [agent_performance[name]['in_progress'] for name in agents_names]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Terminés',
        x=agents_names,
        y=done_counts,
        marker_color='#2ca02c'
    ))
    
    fig.add_trace(go.Bar(
        name='En cours',
        x=agents_names,
        y=in_progress_counts,
        marker_color='#1f77b4'
    ))
    
    fig.add_trace(go.Bar(
        name='En attente',
        x=agents_names,
        y=pending_counts,
        marker_color='#ffd700'
    ))
    
    fig.update_layout(
        title={
            'text': "Performance des agents",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title="Agents",
        yaxis_title="Nombre de tickets",
        barmode='stack',
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

def create_category_distribution_chart(tickets):
    """Crée un graphique de distribution par catégorie de service"""
    category_counts = {}
    
    for ticket in tickets:
        category = ticket.get('categorie_service', 'Non définie')
        category_counts[category] = category_counts.get(category, 0) + 1
    
    if not category_counts:
        return None
    
    # Trier par ordre décroissant
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    categories, counts = zip(*sorted_categories)
    
    fig = go.Figure(data=[go.Bar(
        x=list(categories),
        y=list(counts),
        marker=dict(
            color=list(counts),
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Nombre de tickets")
        ),
        text=list(counts),
        textposition='outside'
    )])
    
    fig.update_layout(
        title={
            'text': "Distribution des tickets par catégorie de service",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title="Catégories de service",
        yaxis_title="Nombre de tickets",
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig

def create_time_evolution_chart(tickets):
    """Crée un graphique d'évolution temporelle des tickets"""
    if not tickets:
        return None
    
    # Simuler des données temporelles (en l'absence de vraies dates)
    dates = []
    ticket_counts = []
    
    # Générer les 7 derniers jours
    for i in range(7):
        date = datetime.now() - timedelta(days=6-i)
        dates.append(date.strftime('%Y-%m-%d'))
        # Simuler des données aléatoires basées sur le nombre total de tickets
        count = np.random.poisson(len(tickets) / 7)
        ticket_counts.append(count)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=ticket_counts,
        mode='lines+markers',
        name='Tickets créés',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8, color='#1f77b4')
    ))
    
    # Ajouter une ligne de tendance
    z = np.polyfit(range(len(dates)), ticket_counts, 1)
    p = np.poly1d(z)
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=p(range(len(dates))),
        mode='lines',
        name='Tendance',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title={
            'text': "Évolution des tickets sur 7 jours",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title="Date",
        yaxis_title="Nombre de tickets",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_priority_chart(tickets):
    """Crée un graphique de répartition par priorité"""
    priority_counts = {}
    priority_order = ['Urgente', 'Haute', 'Normale', 'Basse']
    priority_colors = ['#d62728', '#ff7f0e', '#2ca02c', '#1f77b4']
    
    for ticket in tickets:
        priority = ticket.get('priorite', 'Normale')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    if not priority_counts:
        return None
    
    # Organiser selon l'ordre de priorité
    ordered_priorities = []
    ordered_counts = []
    ordered_colors = []
    
    for i, priority in enumerate(priority_order):
        if priority in priority_counts:
            ordered_priorities.append(priority)
            ordered_counts.append(priority_counts[priority])
            ordered_colors.append(priority_colors[i])
    
    fig = go.Figure(data=[go.Bar(
        x=ordered_priorities,
        y=ordered_counts,
        marker=dict(color=ordered_colors),
        text=ordered_counts,
        textposition='outside'
    )])
    
    fig.update_layout(
        title={
            'text': "Répartition des tickets par priorité",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        xaxis_title="Niveau de priorité",
        yaxis_title="Nombre de tickets",
        height=400
    )
    
    return fig

def display_kpi_cards(metrics):
    """Affiche les cartes KPI"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{metrics['total_agents']}</p>
            <p class="metric-label">👥 Agents totaux</p>
            <p class="metric-delta">
                Transaction: {metrics['agents_transaction']} | 
                Conseil: {metrics['agents_conseil']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{metrics['total_tickets']}</p>
            <p class="metric-label">🎫 Tickets totaux</p>
            <p class="metric-delta">
                +{metrics['pending_tickets']} en attente
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{metrics['completion_rate']:.1f}%</p>
            <p class="metric-label">✅ Taux de completion</p>
            <p class="metric-delta">
                {metrics['done_tickets']} tickets terminés
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        efficiency_score = 100 - metrics['pending_rate'] if metrics['total_tickets'] > 0 else 100
        st.markdown(f"""
        <div class="metric-container">
            <p class="metric-value">{efficiency_score:.1f}%</p>
            <p class="metric-label">⚡ Score d'efficacité</p>
            <p class="metric-delta">
                {metrics['in_progress_tickets']} en cours
            </p>
        </div>
        """, unsafe_allow_html=True)

def main():
    # En-tête du dashboard
    st.markdown("""
    <div class="dashboard-header">
        <h1>📊 Tableau de Bord Smart Agence</h1>
        <p>Vue d'ensemble des performances et statistiques en temps réel</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Récupération des données
    with st.spinner("Chargement des données..."):
        agents = get_api_data("agents")
        tickets = get_api_data("tickets")
    
    if not agents and not tickets:
        st.error("🚨 Impossible de récupérer les données. Vérifiez que l'API est démarrée sur http://localhost:8000")
        st.info("💡 Assurez-vous que le serveur FastAPI est en cours d'exécution.")
        return
    
    # Calcul des métriques
    metrics = calculate_metrics(agents, tickets)
    
    # Affichage des KPI
    display_kpi_cards(metrics)
    
    st.divider()
    
    # Section des graphiques
    st.subheader("📈 Analyses détaillées")
    
    # Première ligne de graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig_status = create_status_distribution_chart(tickets)
            if fig_status:
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("Aucune donnée de statut disponible")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig_priority = create_priority_chart(tickets)
            if fig_priority:
                st.plotly_chart(fig_priority, use_container_width=True)
            else:
                st.info("Aucune donnée de priorité disponible")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Deuxième ligne de graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig_performance = create_agent_performance_chart(agents, tickets)
            if fig_performance:
                st.plotly_chart(fig_performance, use_container_width=True)
            else:
                st.info("Aucune donnée de performance disponible")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig_category = create_category_distribution_chart(tickets)
            if fig_category:
                st.plotly_chart(fig_category, use_container_width=True)
            else:
                st.info("Aucune donnée de catégorie disponible")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Graphique d'évolution temporelle (pleine largeur)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig_evolution = create_time_evolution_chart(tickets)
    if fig_evolution:
        st.plotly_chart(fig_evolution, use_container_width=True)
    else:
        st.info("Aucune donnée temporelle disponible")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Section des détails
    st.divider()
    st.subheader("📋 Détails des données")
    
    tab1, tab2 = st.tabs(["Résumé agents", "Résumé tickets"])
    
    with tab1:
        if agents:
            df_agents = pd.DataFrame(agents)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total agents", len(agents))
                if 'categorie' in df_agents.columns:
                    st.write("**Répartition par catégorie:**")
                    category_counts = df_agents['categorie'].value_counts()
                    for category, count in category_counts.items():
                        st.write(f"- {category.title()}: {count}")
            
            with col2:
                if 'annee_naissance' in df_agents.columns:
                    current_year = datetime.now().year
                    df_agents['age'] = current_year - df_agents['annee_naissance']
                    avg_age = df_agents['age'].mean()
                    st.metric("Âge moyen", f"{avg_age:.1f} ans")
                    
                    st.write("**Statistiques d'âge:**")
                    st.write(f"- Plus jeune: {df_agents['age'].min()} ans")
                    st.write(f"- Plus âgé: {df_agents['age'].max()} ans")
        else:
            st.info("Aucun agent enregistré")
    
    with tab2:
        if tickets:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total tickets", metrics['total_tickets'])
                st.write("**Répartition par statut:**")
                st.write(f"- En attente: {metrics['pending_tickets']}")
                st.write(f"- En cours: {metrics['in_progress_tickets']}")
                st.write(f"- Terminés: {metrics['done_tickets']}")
                st.write(f"- Annulés: {metrics['canceled_tickets']}")
            
            with col2:
                st.metric("Taux de réussite", f"{metrics['completion_rate']:.1f}%")
                
                if tickets:
                    df_tickets = pd.DataFrame(tickets)
                    if 'categorie_service' in df_tickets.columns:
                        st.write("**Top 3 des services:**")
                        top_services = df_tickets['categorie_service'].value_counts().head(3)
                        for i, (service, count) in enumerate(top_services.items(), 1):
                            st.write(f"{i}. {service}: {count} tickets")
        else:
            st.info("Aucun ticket créé")
    
    # Footer avec informations de mise à jour
    st.divider()
    st.caption(f"🔄 Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    
    # Auto-refresh option
    if st.checkbox("🔄 Actualisation automatique (30s)"):
        st.rerun()

if __name__ == "__main__":
    main()