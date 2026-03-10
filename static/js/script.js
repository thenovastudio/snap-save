/* ==========================================================================
   SnapSave - Frontend Logic
   ========================================================================== */

(() => {
    'use strict';

    // -----------------------------------------------------------------------
    // DOM References
    // -----------------------------------------------------------------------
    const urlInput       = document.getElementById('urlInput');
    const pasteBtn       = document.getElementById('pasteBtn');
    const fetchBtn       = document.getElementById('fetchBtn');
    const resultsSection = document.getElementById('results');
    const skeletonSection = document.getElementById('skeleton');
    const resultThumb    = document.getElementById('resultThumb');
    const resultDuration = document.getElementById('resultDuration');
    const resultPlatform = document.getElementById('resultPlatform');
    const resultTitle    = document.getElementById('resultTitle');
    const resultUploader = document.getElementById('resultUploader');
    const qualitySelect  = document.getElementById('qualitySelect');
    const downloadBtn    = document.getElementById('downloadBtn');
    const toastContainer = document.getElementById('toastContainer');

    // Current video data (set after info fetch)
    let currentVideo = null;

    // -----------------------------------------------------------------------
    // Utility: URL validation
    // -----------------------------------------------------------------------
    function isValidUrl(str) {
        try {
            const u = new URL(str);
            return u.protocol === 'http:' || u.protocol === 'https:';
        } catch {
            return false;
        }
    }

    // -----------------------------------------------------------------------
    // Toast Notification System
    // -----------------------------------------------------------------------
    function showToast(message, type = 'info', duration = 5000) {
        const icons = {
            error:   'fas fa-exclamation-circle',
            success: 'fas fa-check-circle',
            info:    'fas fa-info-circle',
        };

        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        toast.innerHTML = `
            <i class="toast__icon ${icons[type] || icons.info}"></i>
            <span class="toast__message">${escapeHtml(message)}</span>
            <button class="toast__close" aria-label="Close">
                <i class="fas fa-times"></i>
            </button>
        `;

        toastContainer.appendChild(toast);

        const closeBtn = toast.querySelector('.toast__close');
        const dismiss = () => {
            toast.classList.add('toast--out');
            toast.addEventListener('animationend', () => toast.remove());
        };
        closeBtn.addEventListener('click', dismiss);

        if (duration > 0) {
            setTimeout(dismiss, duration);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // -----------------------------------------------------------------------
    // Format file size
    // -----------------------------------------------------------------------
    function formatSize(bytes) {
        if (!bytes) return '';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
        return (bytes / 1073741824).toFixed(2) + ' GB';
    }

    // -----------------------------------------------------------------------
    // Loading state helpers
    // -----------------------------------------------------------------------
    function setFetchLoading(loading) {
        const text   = fetchBtn.querySelector('.btn__text');
        const loader = fetchBtn.querySelector('.btn__loader');
        if (loading) {
            text.hidden   = true;
            loader.hidden = false;
            fetchBtn.disabled = true;
            urlInput.disabled = true;
        } else {
            text.hidden   = false;
            loader.hidden = true;
            fetchBtn.disabled = false;
            urlInput.disabled = false;
        }
    }

    function setDownloadLoading(loading) {
        const text   = downloadBtn.querySelector('.btn__text');
        const loader = downloadBtn.querySelector('.btn__loader');
        if (loading) {
            text.hidden   = true;
            loader.hidden = false;
            downloadBtn.disabled = true;
        } else {
            text.hidden   = false;
            loader.hidden = true;
            downloadBtn.disabled = false;
        }
    }

    function showSkeleton() {
        resultsSection.hidden = true;
        skeletonSection.hidden = false;
    }

    function hideSkeleton() {
        skeletonSection.hidden = true;
    }

    // -----------------------------------------------------------------------
    // Fetch Video Info
    // -----------------------------------------------------------------------
    async function fetchVideoInfo(url) {
        if (!url) {
            showToast('Please paste a video URL.', 'error');
            urlInput.focus();
            return;
        }
        if (!isValidUrl(url)) {
            showToast('That doesn\'t look like a valid URL. Please check and try again.', 'error');
            urlInput.focus();
            return;
        }

        setFetchLoading(true);
        showSkeleton();
        resultsSection.hidden = true;

        try {
            const resp = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });

            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.error || 'Failed to fetch video info.');
            }

            currentVideo = data;
            populateResults(data);
            showToast('Video info loaded!', 'success', 3000);

        } catch (err) {
            hideSkeleton();
            showToast(err.message || 'Something went wrong. Please try again.', 'error');
        } finally {
            setFetchLoading(false);
        }
    }

    // -----------------------------------------------------------------------
    // Populate Results
    // -----------------------------------------------------------------------
    function populateResults(data) {
        // Thumbnail
        if (data.thumbnail) {
            resultThumb.src = data.thumbnail;
            resultThumb.alt = data.title || 'Video thumbnail';
        } else {
            resultThumb.src = '';
            resultThumb.alt = 'No thumbnail available';
        }

        // Duration
        if (data.duration) {
            resultDuration.textContent = data.duration;
            resultDuration.hidden = false;
        } else {
            resultDuration.hidden = true;
        }

        // Platform badge
        if (data.platform) {
            resultPlatform.innerHTML = `<i class="${escapeHtml(data.platform.icon)}"></i> ${escapeHtml(data.platform.name)}`;
            resultPlatform.style.color = data.platform.color || '';
            resultPlatform.hidden = false;
        } else {
            resultPlatform.innerHTML = '<i class="fas fa-video"></i> Video';
            resultPlatform.style.color = '';
            resultPlatform.hidden = false;
        }

        // Title
        resultTitle.textContent = data.title || 'Untitled Video';

        // Uploader
        if (data.uploader) {
            resultUploader.textContent = data.uploader;
            resultUploader.hidden = false;
        } else {
            resultUploader.hidden = true;
        }

        // Quality selector
        qualitySelect.innerHTML = '';

        // Add a "Best" default option
        const bestOpt = document.createElement('option');
        bestOpt.value = 'best';
        bestOpt.textContent = 'Best Quality (auto)';
        qualitySelect.appendChild(bestOpt);

        if (data.formats && data.formats.length) {
            data.formats.forEach(f => {
                // Skip very low quality or audio-only for the main list
                const label = buildFormatLabel(f);
                const opt = document.createElement('option');
                opt.value = f.format_id;
                opt.textContent = label;
                qualitySelect.appendChild(opt);
            });
        }

        hideSkeleton();
        resultsSection.hidden = false;

        // Smooth scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }

    function buildFormatLabel(f) {
        let parts = [];
        if (f.quality) parts.push(f.quality);
        if (f.ext) parts.push(f.ext.toUpperCase());

        let meta = [];
        if (f.has_video && f.has_audio) meta.push('video+audio');
        else if (f.has_video) meta.push('video only');
        else if (f.has_audio) meta.push('audio only');

        if (f.filesize) meta.push(formatSize(f.filesize));

        let label = parts.join(' - ');
        if (meta.length) label += ` (${meta.join(', ')})`;
        return label;
    }

    // -----------------------------------------------------------------------
    // Download Video
    // -----------------------------------------------------------------------
    async function downloadVideo() {
        if (!currentVideo || !currentVideo.url) {
            showToast('No video selected. Fetch video info first.', 'error');
            return;
        }

        const formatId = qualitySelect.value;
        setDownloadLoading(true);
        showToast('Starting download... This may take a moment.', 'info', 4000);

        try {
            const resp = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: currentVideo.url,
                    format_id: formatId,
                }),
            });

            if (!resp.ok) {
                let errMsg = 'Download failed.';
                try {
                    const errData = await resp.json();
                    errMsg = errData.error || errMsg;
                } catch {}
                throw new Error(errMsg);
            }

            // Extract filename from Content-Disposition header
            const disposition = resp.headers.get('Content-Disposition') || '';
            let filename = 'video.mp4';
            const match = disposition.match(/filename="?([^"\n]+)"?/i);
            if (match) filename = match[1].trim();

            // Stream to blob and trigger download
            const blob = await resp.blob();
            const blobUrl = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();

            setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
            showToast('Download complete!', 'success');

        } catch (err) {
            showToast(err.message || 'Download failed. Please try again.', 'error');
        } finally {
            setDownloadLoading(false);
        }
    }

    // -----------------------------------------------------------------------
    // Paste from Clipboard
    // -----------------------------------------------------------------------
    async function pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                urlInput.value = text.trim();
                urlInput.focus();
                showToast('Pasted from clipboard!', 'info', 2000);
            }
        } catch {
            showToast('Could not access clipboard. Please paste manually.', 'error');
        }
    }

    // -----------------------------------------------------------------------
    // Event Listeners
    // -----------------------------------------------------------------------

    // Fetch button click
    fetchBtn.addEventListener('click', () => {
        fetchVideoInfo(urlInput.value.trim());
    });

    // Enter key in input
    urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            fetchVideoInfo(urlInput.value.trim());
        }
    });

    // Paste button
    pasteBtn.addEventListener('click', pasteFromClipboard);

    // Download button
    downloadBtn.addEventListener('click', downloadVideo);

    // Auto-detect paste event on input
    urlInput.addEventListener('paste', (e) => {
        // Allow the paste to complete, then auto-fetch after a short delay
        setTimeout(() => {
            const val = urlInput.value.trim();
            if (val && isValidUrl(val)) {
                fetchVideoInfo(val);
            }
        }, 150);
    });

    // Focus input on page load
    urlInput.focus();

})();