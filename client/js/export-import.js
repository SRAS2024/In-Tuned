/**
 * Export/Import Module for In-Tuned
 * Handles data export and import functionality
 */

const DataExport = (function() {
  'use strict';

  /**
   * Export journals to JSON format
   * @param {Array} journals - Journal entries
   * @returns {string} JSON string
   */
  function toJSON(journals) {
    const exportData = {
      version: '1.0',
      exportedAt: new Date().toISOString(),
      source: 'In-Tuned',
      entries: journals.map(journal => ({
        id: journal.id,
        title: journal.title || 'Untitled',
        content: journal.journal_text || journal.journalText || '',
        sourceText: journal.source_text || journal.sourceText || '',
        analysis: journal.analysis_json || journal.analysisSnapshot || null,
        isPinned: journal.is_pinned || journal.isPinned || false,
        createdAt: journal.created_at || journal.createdAt,
        updatedAt: journal.updated_at || journal.updatedAt
      }))
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Export journals to CSV format
   * @param {Array} journals - Journal entries
   * @returns {string} CSV string
   */
  function toCSV(journals) {
    const headers = [
      'ID',
      'Title',
      'Content',
      'Source Text',
      'Dominant Emotion',
      'Current Emotion',
      'Is Pinned',
      'Created At',
      'Updated At'
    ];

    const rows = journals.map(journal => {
      const analysis = journal.analysis_json || journal.analysisSnapshot || {};
      const results = analysis.results || {};

      return [
        journal.id,
        escapeCSV(journal.title || 'Untitled'),
        escapeCSV(journal.journal_text || journal.journalText || ''),
        escapeCSV(journal.source_text || journal.sourceText || ''),
        results.dominant?.label || results.dominant || '',
        results.current?.label || results.current || '',
        journal.is_pinned || journal.isPinned ? 'Yes' : 'No',
        journal.created_at || journal.createdAt || '',
        journal.updated_at || journal.updatedAt || ''
      ].join(',');
    });

    return [headers.join(','), ...rows].join('\n');
  }

  /**
   * Escape value for CSV
   * @param {string} value - Value to escape
   * @returns {string} Escaped value
   */
  function escapeCSV(value) {
    if (value === null || value === undefined) return '';
    const str = String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  }

  /**
   * Export journals to Markdown format
   * @param {Array} journals - Journal entries
   * @returns {string} Markdown string
   */
  function toMarkdown(journals) {
    const lines = [
      '# In-Tuned Journal Export',
      '',
      `Exported: ${new Date().toLocaleString()}`,
      '',
      `Total Entries: ${journals.length}`,
      '',
      '---',
      ''
    ];

    journals.forEach((journal, index) => {
      const analysis = journal.analysis_json || journal.analysisSnapshot || {};
      const results = analysis.results || {};
      const date = new Date(journal.created_at || journal.createdAt);

      lines.push(`## ${index + 1}. ${journal.title || 'Untitled'}`);
      lines.push('');
      lines.push(`**Date:** ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`);

      if (results.dominant) {
        const dominant = results.dominant.label || results.dominant;
        lines.push(`**Dominant Emotion:** ${dominant}`);
      }

      if (results.current) {
        const current = results.current.label || results.current;
        lines.push(`**Current Emotion:** ${current}`);
      }

      lines.push('');

      if (journal.source_text || journal.sourceText) {
        lines.push('### Original Text');
        lines.push('');
        lines.push('> ' + (journal.source_text || journal.sourceText).replace(/\n/g, '\n> '));
        lines.push('');
      }

      if (journal.journal_text || journal.journalText) {
        lines.push('### Journal Entry');
        lines.push('');
        lines.push(journal.journal_text || journal.journalText);
        lines.push('');
      }

      lines.push('---');
      lines.push('');
    });

    return lines.join('\n');
  }

  /**
   * Export journals to plain text format
   * @param {Array} journals - Journal entries
   * @returns {string} Plain text string
   */
  function toText(journals) {
    const lines = [
      'IN-TUNED JOURNAL EXPORT',
      '========================',
      '',
      `Exported: ${new Date().toLocaleString()}`,
      `Total Entries: ${journals.length}`,
      '',
      '========================',
      ''
    ];

    journals.forEach((journal, index) => {
      const date = new Date(journal.created_at || journal.createdAt);

      lines.push(`Entry ${index + 1}: ${journal.title || 'Untitled'}`);
      lines.push(`Date: ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`);
      lines.push('');

      if (journal.source_text || journal.sourceText) {
        lines.push('Original Text:');
        lines.push(journal.source_text || journal.sourceText);
        lines.push('');
      }

      if (journal.journal_text || journal.journalText) {
        lines.push('Journal:');
        lines.push(journal.journal_text || journal.journalText);
        lines.push('');
      }

      lines.push('------------------------');
      lines.push('');
    });

    return lines.join('\n');
  }

  /**
   * Download data as a file
   * @param {string} data - Data to download
   * @param {string} filename - Filename
   * @param {string} mimeType - MIME type
   */
  function downloadFile(data, filename, mimeType) {
    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }

  /**
   * Export journals in specified format
   * @param {Array} journals - Journal entries
   * @param {string} format - Export format (json, csv, markdown, text)
   */
  function exportJournals(journals, format = 'json') {
    const timestamp = new Date().toISOString().split('T')[0];
    let data, filename, mimeType;

    switch (format.toLowerCase()) {
      case 'json':
        data = toJSON(journals);
        filename = `in-tuned-export-${timestamp}.json`;
        mimeType = 'application/json';
        break;

      case 'csv':
        data = toCSV(journals);
        filename = `in-tuned-export-${timestamp}.csv`;
        mimeType = 'text/csv';
        break;

      case 'markdown':
      case 'md':
        data = toMarkdown(journals);
        filename = `in-tuned-export-${timestamp}.md`;
        mimeType = 'text/markdown';
        break;

      case 'text':
      case 'txt':
        data = toText(journals);
        filename = `in-tuned-export-${timestamp}.txt`;
        mimeType = 'text/plain';
        break;

      default:
        throw new Error(`Unsupported format: ${format}`);
    }

    downloadFile(data, filename, mimeType);

    if (typeof UI !== 'undefined') {
      UI.toast(`Exported ${journals.length} entries as ${format.toUpperCase()}`, 'success');
    }
  }

  /**
   * Parse imported JSON data
   * @param {string} jsonString - JSON string
   * @returns {Array} Parsed journal entries
   */
  function parseJSON(jsonString) {
    const data = JSON.parse(jsonString);

    // Handle different export formats
    if (data.entries && Array.isArray(data.entries)) {
      return data.entries.map(normalizeEntry);
    } else if (Array.isArray(data)) {
      return data.map(normalizeEntry);
    }

    throw new Error('Invalid JSON format');
  }

  /**
   * Normalize entry to consistent format
   * @param {Object} entry - Raw entry
   * @returns {Object} Normalized entry
   */
  function normalizeEntry(entry) {
    return {
      title: entry.title || 'Imported Entry',
      journal_text: entry.content || entry.journal_text || entry.journalText || '',
      source_text: entry.sourceText || entry.source_text || '',
      analysis_json: entry.analysis || entry.analysis_json || entry.analysisSnapshot || null,
      is_pinned: entry.isPinned || entry.is_pinned || false,
      created_at: entry.createdAt || entry.created_at || new Date().toISOString()
    };
  }

  /**
   * Import journals from file
   * @param {File} file - File to import
   * @returns {Promise<Array>} Imported entries
   */
  async function importFromFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const content = e.target.result;

          if (file.name.endsWith('.json')) {
            const entries = parseJSON(content);
            resolve(entries);
          } else {
            reject(new Error('Only JSON files are supported for import'));
          }
        } catch (error) {
          reject(new Error(`Failed to parse file: ${error.message}`));
        }
      };

      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  /**
   * Show import dialog
   * @param {Function} onImport - Callback with imported entries
   */
  function showImportDialog(onImport) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';

    input.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        const entries = await importFromFile(file);

        if (typeof UI !== 'undefined') {
          const confirmed = await UI.confirm(
            `Import ${entries.length} journal entries? This will add them to your existing entries.`,
            {
              title: 'Confirm Import',
              confirmText: 'Import',
              cancelText: 'Cancel'
            }
          );

          if (confirmed && onImport) {
            onImport(entries);
            UI.toast(`Successfully imported ${entries.length} entries`, 'success');
          }
        } else if (onImport) {
          onImport(entries);
        }
      } catch (error) {
        if (typeof UI !== 'undefined') {
          UI.toast(error.message, 'error');
        } else {
          console.error('Import error:', error);
        }
      }
    });

    input.click();
  }

  /**
   * Show export dialog with format options
   * @param {Array} journals - Journals to export
   */
  function showExportDialog(journals) {
    if (!journals || journals.length === 0) {
      if (typeof UI !== 'undefined') {
        UI.toast('No entries to export', 'warning');
      }
      return;
    }

    const overlay = document.createElement('div');
    overlay.className = 'export-dialog-overlay';
    overlay.innerHTML = `
      <div class="export-dialog" role="dialog" aria-modal="true">
        <h3>Export Journals</h3>
        <p>Choose export format:</p>
        <div class="export-options">
          <button class="export-option" data-format="json">
            <span class="export-icon">{ }</span>
            <span class="export-label">JSON</span>
            <span class="export-desc">Full data backup</span>
          </button>
          <button class="export-option" data-format="csv">
            <span class="export-icon">📊</span>
            <span class="export-label">CSV</span>
            <span class="export-desc">Spreadsheet compatible</span>
          </button>
          <button class="export-option" data-format="markdown">
            <span class="export-icon">📝</span>
            <span class="export-label">Markdown</span>
            <span class="export-desc">Formatted text</span>
          </button>
          <button class="export-option" data-format="text">
            <span class="export-icon">📄</span>
            <span class="export-label">Plain Text</span>
            <span class="export-desc">Simple readable format</span>
          </button>
        </div>
        <div class="export-actions">
          <button class="btn btn-secondary export-cancel">Cancel</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    // Handle format selection
    overlay.querySelectorAll('.export-option').forEach(btn => {
      btn.addEventListener('click', () => {
        const format = btn.dataset.format;
        exportJournals(journals, format);
        overlay.remove();
      });
    });

    // Handle cancel
    overlay.querySelector('.export-cancel').addEventListener('click', () => {
      overlay.remove();
    });

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.remove();
      }
    });
  }

  return {
    toJSON,
    toCSV,
    toMarkdown,
    toText,
    exportJournals,
    importFromFile,
    showImportDialog,
    showExportDialog,
    downloadFile
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DataExport;
}
