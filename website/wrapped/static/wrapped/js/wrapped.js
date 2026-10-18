/* TOSTI Wrapped: story-style slides in a popup; in December an invitation offers to open it once, and the menu always can. */
(function () {
    "use strict";

    const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const COUNT_DURATION_MS = 1200;

    function formatNumber(value, plain) {
        return plain ? String(value) : value.toLocaleString("en-US");
    }

    function animateCount(element) {
        const target = parseInt(element.dataset.countTo, 10);
        const from = parseInt(element.dataset.countFrom || "0", 10);
        const plain = "countPlain" in element.dataset;
        if (REDUCED_MOTION || Number.isNaN(target)) {
            return;
        }
        const start = performance.now();
        const step = (now) => {
            const progress = Math.min((now - start) / COUNT_DURATION_MS, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = formatNumber(Math.round(from + (target - from) * eased), plain);
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }

    /* -------------------- Share image -------------------- */

    const SHARE_WIDTH = 1080;
    const SHARE_HEIGHT = 1920;
    const SHARE_MARGIN = 110;
    const SHARE_FONT = "Neucha, sans-serif";

    function cssToken(name, fallback) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
    }

    function loadImage(src) {
        return new Promise((resolve) => {
            const image = new Image();
            image.onload = () => resolve(image);
            image.onerror = () => resolve(null);
            image.src = src;
        });
    }

    /* Split text into lines of at most maxWidth, shrinking the font until it fits in maxLines. */
    function fitText(context, text, maxWidth, maxLines, fontSize, minFontSize) {
        for (let size = fontSize; size >= minFontSize; size -= 4) {
            context.font = `${size}px ${SHARE_FONT}`;
            const lines = [];
            let line = "";
            for (const word of text.split(" ")) {
                const candidate = line ? `${line} ${word}` : word;
                if (context.measureText(candidate).width <= maxWidth || !line) {
                    line = candidate;
                } else {
                    lines.push(line);
                    line = word;
                }
            }
            lines.push(line);
            if (lines.length <= maxLines || size - 4 < minFontSize) {
                if (lines.length > maxLines) {
                    lines.length = maxLines;
                    lines[maxLines - 1] += "…";
                }
                return { lines, size };
            }
        }
    }

    async function renderShareImage(canvas, data) {
        const context = canvas.getContext("2d");
        canvas.width = SHARE_WIDTH;
        canvas.height = SHARE_HEIGHT;
        const primary = cssToken("--primary", "#e8b365");
        const white = cssToken("--primary-contrast", "#ffffff");
        const muted = "rgba(255, 255, 255, 0.7)";

        try {
            await document.fonts.load(`80px ${SHARE_FONT}`);
        } catch (error) {
            // Fall back to the default font.
        }

        const background = context.createLinearGradient(0, 0, SHARE_WIDTH, SHARE_HEIGHT);
        background.addColorStop(0, cssToken("--primary-hover", "#c8831e"));
        background.addColorStop(0.55, "#3a2208");
        background.addColorStop(1, "#140b02");
        context.fillStyle = background;
        context.fillRect(0, 0, SHARE_WIDTH, SHARE_HEIGHT);

        context.fillStyle = primary;
        context.globalAlpha = 0.14;
        [[SHARE_WIDTH * 0.95, 160, 340], [40, SHARE_HEIGHT * 0.62, 280], [SHARE_WIDTH * 0.8, SHARE_HEIGHT * 0.95, 220]]
            .forEach(([x, y, radius]) => {
                context.beginPath();
                context.arc(x, y, radius, 0, Math.PI * 2);
                context.fill();
            });
        context.globalAlpha = 1;

        // With a personality, its illustration takes the place of the logo; the logo then goes next to the footer.
        const [logo, art] = await Promise.all([loadImage(data.logo), data.art ? loadImage(data.art) : null]);
        if (art) {
            context.drawImage(art, (SHARE_WIDTH - 340) / 2, 60, 340, 340);
        } else if (logo) {
            context.drawImage(logo, (SHARE_WIDTH - 220) / 2, 120, 220, 220);
        }
        // The illustration is taller than the logo, so move everything below it down.
        const offset = art ? 40 : 0;

        context.textAlign = "center";
        context.textBaseline = "alphabetic";
        context.fillStyle = white;
        context.font = `56px ${SHARE_FONT}`;
        if ("letterSpacing" in context) {
            context.letterSpacing = "10px";
        }
        context.fillText(data.title.toUpperCase(), SHARE_WIDTH / 2, 430 + offset);
        if ("letterSpacing" in context) {
            context.letterSpacing = "0px";
        }
        context.fillStyle = primary;
        // Shrink the year if it doesn't fit, e.g. for a lecture year like 2026/2027.
        let yearSize = 220;
        do {
            context.font = `bold ${yearSize}px ${SHARE_FONT}`;
            yearSize -= 10;
        } while (context.measureText(String(data.year)).width > SHARE_WIDTH - 2 * SHARE_MARGIN && yearSize > 80);
        context.fillText(String(data.year), SHARE_WIDTH / 2, 640 + offset);

        context.textAlign = "left";
        let y = 790 + offset;
        const maxWidth = SHARE_WIDTH - 2 * SHARE_MARGIN;
        const available = SHARE_HEIGHT - 200 - y;
        const perLine = Math.min(220, available / Math.max(data.lines.length, 1));
        data.lines.forEach((line) => {
            context.fillStyle = muted;
            context.font = `40px ${SHARE_FONT}`;
            context.fillText(line.label.toUpperCase(), SHARE_MARGIN, y);
            const value = fitText(context, line.value, maxWidth, 2, 84, 48);
            context.fillStyle = white;
            value.lines.forEach((text, index) => {
                context.fillText(text, SHARE_MARGIN, y + 20 + value.size * (index + 1));
            });
            y += Math.max(perLine, 60 + value.size * value.lines.length + 40);
        });

        context.textAlign = "center";
        context.fillStyle = muted;
        context.font = `44px ${SHARE_FONT}`;
        if (art && logo) {
            const footerWidth = context.measureText(data.footer).width;
            const logoSize = 64;
            const gap = 20;
            const left = (SHARE_WIDTH - footerWidth - logoSize - gap) / 2;
            context.drawImage(logo, left, SHARE_HEIGHT - 110 - 48, logoSize, logoSize);
            context.textAlign = "left";
            context.fillText(data.footer, left + logoSize + gap, SHARE_HEIGHT - 110);
        } else {
            context.fillText(data.footer, SHARE_WIDTH / 2, SHARE_HEIGHT - 110);
        }
    }

    function canvasToFile(canvas, name) {
        return new Promise((resolve) => {
            canvas.toBlob((blob) => resolve(new File([blob], name, { type: "image/png" })), "image/png");
        });
    }

    function initShare(slide) {
        const canvas = slide.querySelector("[data-wrapped-share-canvas]");
        const data = JSON.parse(slide.querySelector('script[type="application/json"]').textContent);
        const fileName = `tosti-wrapped-${data.year.replace("/", "-")}.png`;
        const downloadButton = slide.querySelector("[data-wrapped-download]");
        const shareButton = slide.querySelector("[data-wrapped-native-share]");
        const rendered = renderShareImage(canvas, data);

        downloadButton.addEventListener("click", async () => {
            await rendered;
            const link = document.createElement("a");
            link.download = fileName;
            link.href = URL.createObjectURL(await canvasToFile(canvas, fileName));
            link.click();
            setTimeout(() => URL.revokeObjectURL(link.href), 1000);
        });

        rendered.then(() => canvasToFile(canvas, fileName)).then((file) => {
            if (!navigator.canShare || !navigator.canShare({ files: [file] })) {
                return;
            }
            shareButton.hidden = false;
            shareButton.addEventListener("click", () => {
                navigator.share({ files: [file], title: `${data.title} ${data.year}` }).catch(() => {
                    // The user cancelled sharing.
                });
            });
        });
    }

    function initStory(story) {
        const slides = Array.from(story.querySelectorAll(".wrapped-slide"));
        const progress = story.querySelector("[data-wrapped-progress]");
        const counter = story.querySelector("[data-wrapped-counter]");
        const previousButton = story.querySelector("[data-wrapped-prev]");
        const nextButton = story.querySelector("[data-wrapped-next]");
        const bars = slides.map(() => progress.appendChild(document.createElement("span")));
        let current = 0;
        let shareInitialised = false;

        function show(index) {
            current = Math.max(0, Math.min(index, slides.length - 1));
            slides.forEach((slide, i) => {
                slide.hidden = i !== current;
            });
            bars.forEach((bar, i) => bar.classList.toggle("is-done", i <= current));
            counter.textContent = `${current + 1} / ${slides.length}`;
            previousButton.disabled = current === 0;
            nextButton.disabled = current === slides.length - 1;
            slides[current].querySelectorAll("[data-count-to]").forEach(animateCount);
            if (!shareInitialised && "wrappedShare" in slides[current].dataset) {
                shareInitialised = true;
                initShare(slides[current]);
            }
        }

        previousButton.addEventListener("click", () => show(current - 1));
        nextButton.addEventListener("click", () => show(current + 1));

        // Like a story: tap the left third to go back, anywhere else to go forward.
        story.querySelector("[data-wrapped-slides]").addEventListener("click", (event) => {
            if (event.target.closest("a, button, canvas")) {
                return;
            }
            const bounds = event.currentTarget.getBoundingClientRect();
            show(event.clientX - bounds.left < bounds.width / 3 ? current - 1 : current + 1);
        });

        story.addEventListener("keydown", (event) => {
            if (event.key === "ArrowLeft") {
                show(current - 1);
            } else if (event.key === "ArrowRight" || event.key === " ") {
                event.preventDefault();
                show(current + 1);
            }
        });

        return show;
    }

    const WRAPPED_HASH = "#wrapped";

    /* The popup is empty until it opens; then the slides are loaded from the server. */
    function initPopup(popup) {
        const modal = bootstrap.Modal.getOrCreateInstance(popup);
        const body = popup.querySelector("[data-wrapped-body]");
        let loaded = null;

        function load() {
            if (loaded === null) {
                loaded = fetch(popup.dataset.storyUrl, { headers: { Accept: "text/html" } })
                    .then((response) => {
                        if (!response.ok) {
                            throw response;
                        }
                        return response.text();
                    })
                    .then((html) => {
                        body.innerHTML = html;
                        return initStory(body.querySelector("[data-wrapped-story]"));
                    })
                    .catch((error) => {
                        loaded = null;
                        throw error;
                    });
            }
            return loaded;
        }

        function open() {
            modal.show();
            load()
                .then((show) => {
                    show(0);
                    body.querySelector("[data-wrapped-story]").focus();
                })
                .catch(() => {
                    body.innerHTML = '<p class="wrapped-loading">Your Wrapped could not be loaded. Please try again later.</p>';
                });
        }

        function markSeen() {
            // Don't invite again for this Wrapped; the menu item can still open it.
            const maxAge = 60 * 60 * 24 * 60;
            document.cookie = `${popup.dataset.seenCookie}=${popup.dataset.seenValue}; max-age=${maxAge}; path=/; SameSite=Lax`;
        }

        // Before taking over the whole screen, first ask whether to open it.
        const invite = document.querySelector("[data-wrapped-invite]");
        invite.querySelector("[data-wrapped-invite-open]").addEventListener("click", () => {
            invite.hidden = true;
            open();
        });
        invite.querySelector("[data-wrapped-invite-dismiss]").addEventListener("click", () => {
            invite.hidden = true;
            markSeen();
        });

        popup.addEventListener("hidden.bs.modal", () => {
            markSeen();
            if (window.location.hash === WRAPPED_HASH) {
                history.replaceState(null, "", window.location.pathname + window.location.search);
            }
        });

        // Links to #wrapped (like the menu item) open the popup on the current page.
        document.addEventListener("click", (event) => {
            const link = event.target.closest(`a[href="${WRAPPED_HASH}"]`);
            if (link) {
                event.preventDefault();
                invite.hidden = true;
                open();
            }
        });

        if (window.location.hash === WRAPPED_HASH) {
            open();
        } else if (popup.dataset.invite === "true") {
            invite.hidden = false;
        }
    }

    function init() {
        document.querySelectorAll("[data-wrapped-popup]").forEach(initPopup);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
