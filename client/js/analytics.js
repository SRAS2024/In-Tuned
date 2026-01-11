/**
 * Analytics Dashboard Module for In-Tuned
 * Displays emotion trends, activity stats, and insights
 */

const Analytics = (function() {
  'use strict';

  // Chart colors for emotions
  const EMOTION_COLORS = {
    anger: '#ef4444',
    disgust: '#84cc16',
    fear: '#a855f7',
    joy: '#fbbf24',
    sadness: '#3b82f6',
    passion: '#ec4899',
    surprise: '#06b6d4'
  };

  // State
  let currentPeriod = '30d';
  let emotionChart = null;
  let activityChart = null;

  /**
   * Initialize the analytics dashboard
   * @param {HTMLElement} container - Dashboard container
   */
  async function init(container) {
    if (!container) return;

    // Render dashboard structure
    container.innerHTML = `
      <div class="analytics-dashboard">
        <div class="analytics-header">
          <h2>Your Emotional Insights</h2>
          <div class="period-selector">
            <button class="period-btn active" data-period="7d">7 Days</button>
            <button class="period-btn" data-period="30d">30 Days</button>
            <button class="period-btn" data-period="90d">90 Days</button>
            <button class="period-btn" data-period="all">All Time</button>
          </div>
        </div>

        <div class="analytics-grid">
          <div class="analytics-card stats-summary">
            <h3>Summary</h3>
            <div class="stats-grid" id="statsSummary">
              <div class="stat-item">
                <span class="stat-value" id="totalEntries">-</span>
                <span class="stat-label">Total Entries</span>
              </div>
              <div class="stat-item">
                <span class="stat-value" id="avgEntriesPerWeek">-</span>
                <span class="stat-label">Avg per Week</span>
              </div>
              <div class="stat-item">
                <span class="stat-value" id="dominantEmotion">-</span>
                <span class="stat-label">Most Common</span>
              </div>
              <div class="stat-item">
                <span class="stat-value" id="currentStreak">-</span>
                <span class="stat-label">Day Streak</span>
              </div>
            </div>
          </div>

          <div class="analytics-card emotion-distribution">
            <h3>Emotion Distribution</h3>
            <div class="chart-container">
              <canvas id="emotionChart"></canvas>
            </div>
            <div class="emotion-legend" id="emotionLegend"></div>
          </div>

          <div class="analytics-card activity-timeline">
            <h3>Activity Timeline</h3>
            <div class="chart-container">
              <canvas id="activityChart"></canvas>
            </div>
          </div>

          <div class="analytics-card insights-panel">
            <h3>Insights</h3>
            <div class="insights-list" id="insightsList">
              <p class="loading-text">Loading insights...</p>
            </div>
          </div>

          <div class="analytics-card emotion-trends">
            <h3>Emotion Trends</h3>
            <div class="trends-list" id="trendsList"></div>
          </div>
        </div>
      </div>
    `;

    // Setup period selector
    setupPeriodSelector(container);

    // Load initial data
    await loadDashboardData();
  }

  /**
   * Setup period selector buttons
   * @param {HTMLElement} container - Dashboard container
   */
  function setupPeriodSelector(container) {
    const buttons = container.querySelectorAll('.period-btn');
    buttons.forEach(btn => {
      btn.addEventListener('click', async () => {
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentPeriod = btn.dataset.period;
        await loadDashboardData();
      });
    });
  }

  /**
   * Load all dashboard data
   */
  async function loadDashboardData() {
    try {
      // Load data in parallel
      const [emotionData, activityData, insights] = await Promise.all([
        loadEmotionData(),
        loadActivityData(),
        loadInsights()
      ]);

      renderSummaryStats(emotionData, activityData);
      renderEmotionChart(emotionData);
      renderActivityChart(activityData);
      renderInsights(insights);
      renderTrends(emotionData);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      UI.toast('Failed to load analytics data', 'error');
    }
  }

  /**
   * Load emotion distribution data
   * @returns {Promise<Object>} Emotion data
   */
  async function loadEmotionData() {
    try {
      if (typeof API !== 'undefined' && API.analytics) {
        return await API.analytics.getEmotionTrends(currentPeriod);
      }
      // Fallback: calculate from journals
      return calculateEmotionDataFromJournals();
    } catch (error) {
      console.error('Failed to load emotion data:', error);
      return { distribution: {}, trends: [] };
    }
  }

  /**
   * Calculate emotion data from local journals
   * @returns {Object} Calculated emotion data
   */
  function calculateEmotionDataFromJournals() {
    // This will be populated from the journals array in main.js
    const journals = window.journals || [];
    const distribution = {
      anger: 0,
      disgust: 0,
      fear: 0,
      joy: 0,
      sadness: 0,
      passion: 0,
      surprise: 0
    };

    let total = 0;

    journals.forEach(journal => {
      const analysis = journal.analysis_json || journal.analysisSnapshot;
      if (analysis && analysis.coreMixture) {
        const mixture = Array.isArray(analysis.coreMixture)
          ? analysis.coreMixture
          : Object.entries(analysis.coreMixture).map(([id, value]) => ({
              id,
              percent: typeof value === 'number' ? value * 100 : value.percent || 0
            }));

        mixture.forEach(item => {
          const emotion = item.id || item.label?.toLowerCase();
          if (distribution.hasOwnProperty(emotion)) {
            distribution[emotion] += item.percent || 0;
            total += item.percent || 0;
          }
        });
      }
    });

    // Normalize to percentages
    if (total > 0) {
      Object.keys(distribution).forEach(key => {
        distribution[key] = (distribution[key] / total) * 100;
      });
    }

    return {
      distribution,
      trends: calculateTrends(journals),
      totalEntries: journals.length
    };
  }

  /**
   * Calculate emotion trends over time
   * @param {Array} journals - Journal entries
   * @returns {Array} Trend data
   */
  function calculateTrends(journals) {
    // Group by week
    const weeklyData = {};

    journals.forEach(journal => {
      const date = new Date(journal.created_at || journal.createdAt);
      const weekStart = getWeekStart(date);
      const key = weekStart.toISOString().split('T')[0];

      if (!weeklyData[key]) {
        weeklyData[key] = { date: key, emotions: {} };
      }

      const analysis = journal.analysis_json || journal.analysisSnapshot;
      if (analysis && analysis.results) {
        const dominant = analysis.results.dominant?.id ||
                        analysis.results.dominant?.label?.toLowerCase() ||
                        analysis.results.dominant;
        if (dominant) {
          weeklyData[key].emotions[dominant] =
            (weeklyData[key].emotions[dominant] || 0) + 1;
        }
      }
    });

    return Object.values(weeklyData).sort((a, b) =>
      new Date(a.date) - new Date(b.date)
    );
  }

  /**
   * Get start of week for a date
   * @param {Date} date - Date
   * @returns {Date} Start of week
   */
  function getWeekStart(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
  }

  /**
   * Load activity data
   * @returns {Promise<Object>} Activity data
   */
  async function loadActivityData() {
    try {
      if (typeof API !== 'undefined' && API.analytics) {
        return await API.analytics.getActivityStats(currentPeriod);
      }
      return calculateActivityFromJournals();
    } catch (error) {
      console.error('Failed to load activity data:', error);
      return { daily: [], streak: 0 };
    }
  }

  /**
   * Calculate activity from local journals
   * @returns {Object} Activity data
   */
  function calculateActivityFromJournals() {
    const journals = window.journals || [];
    const dailyMap = {};

    journals.forEach(journal => {
      const date = new Date(journal.created_at || journal.createdAt);
      const key = date.toISOString().split('T')[0];
      dailyMap[key] = (dailyMap[key] || 0) + 1;
    });

    // Convert to array sorted by date
    const daily = Object.entries(dailyMap)
      .map(([date, count]) => ({ date, count }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    // Calculate streak
    let streak = 0;
    const today = new Date().toISOString().split('T')[0];
    let currentDate = new Date(today);

    while (true) {
      const key = currentDate.toISOString().split('T')[0];
      if (dailyMap[key]) {
        streak++;
        currentDate.setDate(currentDate.getDate() - 1);
      } else {
        break;
      }
    }

    return { daily, streak };
  }

  /**
   * Load insights
   * @returns {Promise<Array>} Insights array
   */
  async function loadInsights() {
    try {
      if (typeof API !== 'undefined' && API.analytics) {
        const response = await API.analytics.getInsights();
        return response.insights || [];
      }
      return generateLocalInsights();
    } catch (error) {
      console.error('Failed to load insights:', error);
      return [];
    }
  }

  /**
   * Generate insights from local data
   * @returns {Array} Generated insights
   */
  function generateLocalInsights() {
    const journals = window.journals || [];
    const insights = [];

    if (journals.length === 0) {
      insights.push({
        type: 'info',
        title: 'Get Started',
        message: 'Create your first journal entry to start tracking your emotions.'
      });
      return insights;
    }

    // Calculate emotion distribution
    const emotionCounts = {};
    let totalAnalyzed = 0;

    journals.forEach(journal => {
      const analysis = journal.analysis_json || journal.analysisSnapshot;
      if (analysis && analysis.results) {
        const dominant = analysis.results.dominant?.label ||
                        analysis.results.dominant?.id ||
                        analysis.results.dominant;
        if (dominant) {
          const key = dominant.toLowerCase();
          emotionCounts[key] = (emotionCounts[key] || 0) + 1;
          totalAnalyzed++;
        }
      }
    });

    // Most common emotion
    const sortedEmotions = Object.entries(emotionCounts)
      .sort((a, b) => b[1] - a[1]);

    if (sortedEmotions.length > 0) {
      const [topEmotion, count] = sortedEmotions[0];
      const percentage = Math.round((count / totalAnalyzed) * 100);
      insights.push({
        type: 'highlight',
        title: 'Dominant Emotion',
        message: `${capitalize(topEmotion)} appears in ${percentage}% of your entries.`
      });
    }

    // Journal frequency
    const daysSinceFirst = journals.length > 0
      ? Math.ceil((Date.now() - new Date(journals[journals.length - 1].created_at || journals[journals.length - 1].createdAt)) / (1000 * 60 * 60 * 24))
      : 0;

    if (daysSinceFirst > 0) {
      const avgPerWeek = Math.round((journals.length / daysSinceFirst) * 7 * 10) / 10;
      insights.push({
        type: 'stat',
        title: 'Writing Frequency',
        message: `You write an average of ${avgPerWeek} entries per week.`
      });
    }

    // Emotional diversity
    const uniqueEmotions = Object.keys(emotionCounts).length;
    if (uniqueEmotions >= 5) {
      insights.push({
        type: 'positive',
        title: 'Emotional Range',
        message: `You've experienced ${uniqueEmotions} different dominant emotions. This emotional diversity is healthy!`
      });
    }

    return insights;
  }

  /**
   * Capitalize first letter
   * @param {string} str - String to capitalize
   * @returns {string} Capitalized string
   */
  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  /**
   * Render summary statistics
   * @param {Object} emotionData - Emotion data
   * @param {Object} activityData - Activity data
   */
  function renderSummaryStats(emotionData, activityData) {
    const journals = window.journals || [];

    document.getElementById('totalEntries').textContent = journals.length;
    document.getElementById('currentStreak').textContent = activityData.streak || 0;

    // Calculate average per week
    if (journals.length > 0) {
      const oldestEntry = journals[journals.length - 1];
      const daysSince = Math.max(1, Math.ceil(
        (Date.now() - new Date(oldestEntry.created_at || oldestEntry.createdAt)) /
        (1000 * 60 * 60 * 24)
      ));
      const avgPerWeek = Math.round((journals.length / daysSince) * 7 * 10) / 10;
      document.getElementById('avgEntriesPerWeek').textContent = avgPerWeek;
    } else {
      document.getElementById('avgEntriesPerWeek').textContent = '0';
    }

    // Find dominant emotion
    const distribution = emotionData.distribution || {};
    const sorted = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
    if (sorted.length > 0 && sorted[0][1] > 0) {
      document.getElementById('dominantEmotion').textContent = capitalize(sorted[0][0]);
    } else {
      document.getElementById('dominantEmotion').textContent = '-';
    }
  }

  /**
   * Render emotion distribution chart
   * @param {Object} emotionData - Emotion data
   */
  function renderEmotionChart(emotionData) {
    const canvas = document.getElementById('emotionChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const distribution = emotionData.distribution || {};

    // Simple pie chart without Chart.js dependency
    const data = Object.entries(distribution)
      .filter(([_, value]) => value > 0)
      .map(([emotion, value]) => ({
        emotion,
        value,
        color: EMOTION_COLORS[emotion] || '#6b7280'
      }));

    if (data.length === 0) {
      ctx.fillStyle = '#6b7280';
      ctx.font = '14px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('No data available', canvas.width / 2, canvas.height / 2);
      return;
    }

    const total = data.reduce((sum, d) => sum + d.value, 0);
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 10;

    let startAngle = -Math.PI / 2;

    data.forEach(item => {
      const sliceAngle = (item.value / total) * 2 * Math.PI;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      ctx.closePath();
      ctx.fillStyle = item.color;
      ctx.fill();

      startAngle += sliceAngle;
    });

    // Render legend
    const legendContainer = document.getElementById('emotionLegend');
    if (legendContainer) {
      legendContainer.innerHTML = data.map(item => `
        <div class="legend-item">
          <span class="legend-color" style="background-color: ${item.color}"></span>
          <span class="legend-label">${capitalize(item.emotion)}</span>
          <span class="legend-value">${Math.round(item.value)}%</span>
        </div>
      `).join('');
    }
  }

  /**
   * Render activity timeline chart
   * @param {Object} activityData - Activity data
   */
  function renderActivityChart(activityData) {
    const canvas = document.getElementById('activityChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const daily = activityData.daily || [];

    if (daily.length === 0) {
      ctx.fillStyle = '#6b7280';
      ctx.font = '14px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('No activity data', canvas.width / 2, canvas.height / 2);
      return;
    }

    // Simple bar chart
    const maxCount = Math.max(...daily.map(d => d.count), 1);
    const barWidth = Math.max(4, (canvas.width - 40) / daily.length - 2);
    const chartHeight = canvas.height - 40;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    daily.forEach((item, index) => {
      const barHeight = (item.count / maxCount) * chartHeight;
      const x = 20 + index * (barWidth + 2);
      const y = canvas.height - 20 - barHeight;

      ctx.fillStyle = '#6366f1';
      ctx.fillRect(x, y, barWidth, barHeight);
    });

    // X-axis label
    ctx.fillStyle = '#6b7280';
    ctx.font = '12px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('Time →', canvas.width / 2, canvas.height - 5);
  }

  /**
   * Render insights
   * @param {Array} insights - Insights array
   */
  function renderInsights(insights) {
    const container = document.getElementById('insightsList');
    if (!container) return;

    if (!insights || insights.length === 0) {
      container.innerHTML = '<p class="no-insights">Keep journaling to unlock insights!</p>';
      return;
    }

    container.innerHTML = insights.map(insight => `
      <div class="insight-item insight-${insight.type || 'info'}">
        <h4 class="insight-title">${UI.escapeHTML(insight.title)}</h4>
        <p class="insight-message">${UI.escapeHTML(insight.message)}</p>
      </div>
    `).join('');
  }

  /**
   * Render emotion trends
   * @param {Object} emotionData - Emotion data
   */
  function renderTrends(emotionData) {
    const container = document.getElementById('trendsList');
    if (!container) return;

    const distribution = emotionData.distribution || {};
    const sorted = Object.entries(distribution)
      .sort((a, b) => b[1] - a[1])
      .filter(([_, value]) => value > 0);

    if (sorted.length === 0) {
      container.innerHTML = '<p class="no-trends">No emotion data yet.</p>';
      return;
    }

    container.innerHTML = sorted.map(([emotion, value]) => `
      <div class="trend-item">
        <div class="trend-header">
          <span class="trend-emotion">${capitalize(emotion)}</span>
          <span class="trend-percent">${Math.round(value)}%</span>
        </div>
        <div class="trend-bar">
          <div class="trend-fill" style="width: ${value}%; background-color: ${EMOTION_COLORS[emotion]}"></div>
        </div>
      </div>
    `).join('');
  }

  /**
   * Refresh dashboard data
   */
  async function refresh() {
    await loadDashboardData();
  }

  return {
    init,
    refresh,
    EMOTION_COLORS
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Analytics;
}
