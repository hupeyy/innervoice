<script>
  import { onMount } from 'svelte';
  
  export let journalEntries = [];
  
  let selectedTimeframe = '7d';
  let sentimentData = [];
  let moodBreakdown = {};
  let emotionalThemes = [];
  let averageSentiment = 0;
  let moodStreak = 0;
  
  // FIXED: Watch BOTH journalEntries AND selectedTimeframe
  $: if (journalEntries && selectedTimeframe) {
    calculateSentimentMetrics();
  }
  
  function calculateSentimentMetrics() {
    if (!journalEntries || journalEntries.length === 0) return;
    
    // Filter entries based on timeframe
    const filteredEntries = filterEntriesByTimeframe(journalEntries, selectedTimeframe);
    
    // Calculate daily sentiment scores
    sentimentData = filteredEntries.map(entry => ({
      date: formatDate(entry.date),
      sentiment: entry.sentimentScore || 0,
      mood: getMoodFromScore(entry.sentimentScore || 0)
    }));
    
    // Calculate mood breakdown
    moodBreakdown = sentimentData.reduce((acc, day) => {
      acc[day.mood] = (acc[day.mood] || 0) + 1;
      return acc;
    }, {});
    
    // Calculate average sentiment
    averageSentiment = sentimentData.length > 0 
      ? sentimentData.reduce((sum, day) => sum + day.sentiment, 0) / sentimentData.length
      : 0;
    
    // Calculate mood streak (consecutive positive days)
    moodStreak = calculatePositiveStreak(sentimentData);
    
    // Extract emotional themes
    emotionalThemes = extractThemes(filteredEntries);
  }
  
  function filterEntriesByTimeframe(entries, timeframe) {
    const now = new Date();
    const days = timeframe === '7d' ? 7 : timeframe === '30d' ? 30 : 90;
    const cutoff = new Date(now.getTime() - (days * 24 * 60 * 60 * 1000));
    
    return entries.filter(entry => new Date(entry.date) >= cutoff);
  }
  
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
  
  function getMoodFromScore(score) {
    if (score >= 0.3) return 'positive';
    if (score <= -0.3) return 'negative';
    return 'neutral';
  }
  
  function calculatePositiveStreak(data) {
    let streak = 0;
    for (let i = data.length - 1; i >= 0; i--) {
      if (data[i].sentiment > 0) {
        streak++;
      } else {
        break;
      }
    }
    return streak;
  }
  
  function extractThemes(entries) {
    const themes = [];
    entries.forEach(entry => {
      if (entry.insights) {
        entry.insights.forEach(insight => {
          const lowerInsight = insight.toLowerCase();
          if (lowerInsight.includes('work') || lowerInsight.includes('stress') || lowerInsight.includes('career')) {
            themes.push('Work & Productivity');
          } else if (lowerInsight.includes('relationship') || lowerInsight.includes('family') || lowerInsight.includes('friend')) {
            themes.push('Relationships');
          } else if (lowerInsight.includes('health') || lowerInsight.includes('exercise') || lowerInsight.includes('wellness')) {
            themes.push('Health & Wellness');
          } else if (lowerInsight.includes('creative') || lowerInsight.includes('hobby') || lowerInsight.includes('art')) {
            themes.push('Creativity & Hobbies');
          }
        });
      }
    });
    
    const themeCount = themes.reduce((acc, theme) => {
      acc[theme] = (acc[theme] || 0) + 1;
      return acc;
    }, {});
    
    return Object.entries(themeCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([theme, count]) => ({ theme, count }));
  }
  
  function getMoodColor(mood) {
    switch (mood) {
      case 'positive': return '#10b981';
      case 'negative': return '#f87171';
      default: return '#6b7280';
    }
  }
  
  function getMoodIcon(mood) {
    switch (mood) {
      case 'positive': return '😊';
      case 'negative': return '😔';
      default: return '😐';
    }
  }
  
  function handleTimeframeChange(timeframe) {
    console.log('Changing timeframe from', selectedTimeframe, 'to', timeframe);
    selectedTimeframe = timeframe;
    console.log('New timeframe set:', selectedTimeframe);
  }
</script>

<div class="sentiment-dashboard">
  <!-- Header with Timeframe Selector -->
  <div class="dashboard-header">
    <h2>🧠 Emotional Insights</h2>
    <div class="timeframe-selector">
      <button 
        class="timeframe-btn {selectedTimeframe === '7d' ? 'active' : ''}"
        on:click={() => handleTimeframeChange('7d')}
      >
        7 Days
      </button>
      <button 
        class="timeframe-btn {selectedTimeframe === '30d' ? 'active' : ''}"
        on:click={() => handleTimeframeChange('30d')}
      >
        30 Days
      </button>
      <button 
        class="timeframe-btn {selectedTimeframe === '90d' ? 'active' : ''}"
        on:click={() => handleTimeframeChange('90d')}
      >
        3 Months
      </button>
    </div>
  </div>

  {#if sentimentData.length === 0}
    <div class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>No Data Yet</h3>
      <p>Keep journaling to see your emotional patterns and insights!</p>
    </div>
  {:else}
    <!-- Key Metrics Row -->
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-icon">📈</div>
        <div class="metric-content">
          <h3>Avg Sentiment</h3>
          <p class="metric-value" style="color: {getMoodColor(getMoodFromScore(averageSentiment))}">
            {averageSentiment.toFixed(2)}
          </p>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-icon">🔥</div>
        <div class="metric-content">
          <h3>Positive Streak</h3>
          <p class="metric-value">{moodStreak} day{moodStreak !== 1 ? 's' : ''}</p>
        </div>
      </div>
      
      <div class="metric-card">
        <div class="metric-icon">📝</div>
        <div class="metric-content">
          <h3>Total Entries</h3>
          <p class="metric-value">{sentimentData.length}</p>
        </div>
      </div>
    </div>

    <!-- Sentiment Trend Chart -->
    <div class="chart-container">
      <h3>Sentiment Over Time</h3>
      <div class="sentiment-chart">
        <svg viewBox="0 0 400 200" class="chart-svg">
          <!-- Grid lines -->
          <line x1="40" y1="50" x2="360" y2="50" stroke="#e5e7eb" stroke-width="1"/>
          <line x1="40" y1="100" x2="360" y2="100" stroke="#d1d5db" stroke-width="2"/>
          <line x1="40" y1="150" x2="360" y2="150" stroke="#e5e7eb" stroke-width="1"/>
          
          <!-- Y-axis labels -->
          <text x="30" y="55" font-size="10" fill="#6b7280" text-anchor="end">1.0</text>
          <text x="30" y="105" font-size="10" fill="#6b7280" text-anchor="end">0.0</text>
          <text x="30" y="155" font-size="10" fill="#6b7280" text-anchor="end">-1.0</text>
          
          <!-- FIXED: Sentiment line with reversed data -->
          {#if sentimentData.length > 1}
            <polyline
              points={sentimentData.slice().reverse().map((point, i) => {
                const x = 40 + (i * (320 / (sentimentData.length - 1)));
                const y = 100 - (point.sentiment * 50);
                return `${x},${y}`;
              }).join(' ')}
              fill="none"
              stroke="#6366f1"
              stroke-width="2"
            />
          {/if}
          
          <!-- FIXED: Data points with reversed data -->
          {#each sentimentData.slice().reverse() as point, i}
            <circle
              cx={40 + (i * (320 / Math.max(sentimentData.length - 1, 1)))}
              cy={100 - (point.sentiment * 50)}
              r="4"
              fill={getMoodColor(point.mood)}
              class="data-point"
            />
          {/each}
          
          <!-- FIXED: X-axis labels with reversed data -->
          {#each sentimentData.slice().reverse() as point, i}
            {#if i % Math.ceil(sentimentData.length / 5) === 0}
              <text
                x={40 + (i * (320 / Math.max(sentimentData.length - 1, 1)))}
                y="185"
                font-size="9"
                fill="#6b7280"
                text-anchor="middle"
              >
                {point.date}
              </text>
            {/if}
          {/each}
        </svg>
      </div>
    </div>


    <!-- Mood Distribution -->
    <div class="mood-section">
      <h3>Mood Distribution</h3>
      <div class="mood-bars">
        {#each Object.entries(moodBreakdown) as [mood, count]}
          <div class="mood-bar">
            <div class="mood-info">
              <span class="mood-icon">{getMoodIcon(mood)}</span>
              <span class="mood-label">{mood}</span>
            </div>
            <div class="bar-container">
              <div 
                class="bar-fill" 
                style="width: {(count / Math.max(...Object.values(moodBreakdown))) * 100}%; background-color: {getMoodColor(mood)}"
              ></div>
              <span class="bar-count">{count}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Emotional Themes -->
    {#if emotionalThemes.length > 0}
      <div class="themes-section">
        <h3>Common Themes</h3>
        <div class="theme-tags">
          {#each emotionalThemes as {theme, count}}
            <div class="theme-tag">
              <span class="theme-name">{theme}</span>
              <span class="theme-count">{count}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .sentiment-dashboard {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
  }
  
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .dashboard-header h2 {
    margin: 0;
    color: #374151;
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .timeframe-selector {
    display: flex;
    gap: 0.5rem;
  }
  
  .timeframe-btn {
    padding: 0.5rem 1rem;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
  }
  
  .timeframe-btn:hover {
    border-color: #6366f1;
    background: #f8fafc;
  }
  
  .timeframe-btn.active {
    border-color: #6366f1;
    background: #6366f1;
    color: white;
  }
  
  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #6b7280;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  
  .metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .metric-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }
  
  .metric-icon {
    font-size: 2rem;
  }
  
  .metric-content h3 {
    margin: 0 0 0.25rem 0;
    font-size: 0.875rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .metric-value {
    margin: 0;
    font-size: 1.5rem;
    font-weight: bold;
    color: #374151;
  }
  
  .chart-container, .mood-section, .themes-section {
    margin-bottom: 2rem;
  }
  
  .chart-container h3, .mood-section h3, .themes-section h3 {
    margin: 0 0 1rem 0;
    color: #374151;
    font-size: 1.125rem;
    font-weight: 600;
  }
  
  .sentiment-chart {
    background: #f9fafb;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #e5e7eb;
  }
  
  .chart-svg {
    width: 100%;
    height: 200px;
  }
  
  .data-point {
    cursor: pointer;
    transition: r 0.2s;
  }
  
  .data-point:hover {
    r: 6;
  }
  
  .mood-bars {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .mood-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .mood-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 100px;
  }
  
  .mood-icon {
    font-size: 1.25rem;
  }
  
  .mood-label {
    font-weight: 500;
    text-transform: capitalize;
  }
  
  .bar-container {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    height: 24px;
  }
  
  .bar-fill {
    height: 100%;
    border-radius: 12px;
    min-width: 2px;
    transition: width 0.3s ease;
  }
  
  .bar-count {
    font-weight: 500;
    color: #6b7280;
    min-width: 20px;
  }
  
  .theme-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  
  .theme-tag {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #f3f4f6;
    border-radius: 20px;
    border: 1px solid #d1d5db;
  }
  
  .theme-name {
    font-weight: 500;
    color: #374151;
  }
  
  .theme-count {
    background: #6366f1;
    color: white;
    font-size: 0.75rem;
    padding: 0.125rem 0.5rem;
    border-radius: 10px;
    font-weight: 600;
  }
  
  @media (max-width: 768px) {
    .dashboard-header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }
    
    .metrics-row {
      grid-template-columns: 1fr;
    }
    
    .mood-bar {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
    
    .bar-container {
      width: 100%;
    }
  }
</style>