const ANNOUNCEMENT_COOKIE = "closed-announcements";

function safeGetCookie() {
    try {
        return get_cookie(ANNOUNCEMENT_COOKIE);
    } catch {
        return null;
    }
}

function sanitizeAnnouncementsArray(closedAnnouncements) {
    if (closedAnnouncements === null || typeof closedAnnouncements !== 'string') {
        return [];
    }
    else {
        try {
            closedAnnouncements = JSON.parse(closedAnnouncements);
        } catch {
            return [];
        }
        if (! Array.isArray(closedAnnouncements)) {
            closedAnnouncements = [];
        }

        for (let i = 0; i < closedAnnouncements.length; i++) {
            if (!Number.isInteger(closedAnnouncements[i])) {
                closedAnnouncements.splice(i, 1);
            }
        }
        return closedAnnouncements;
    }
}
function close_announcement(announcementId) {
    let announcementElement = document.getElementById("announcement-" + announcementId);

    if (announcementElement !== null) {
        announcementElement.remove();
    }

    let closedAnnouncements = safeGetCookie();

    if (closedAnnouncements === null) {
        closedAnnouncements = [];
    } else {
        closedAnnouncements = sanitizeAnnouncementsArray(closedAnnouncements);
    }

    if (!closedAnnouncements.includes(announcementId)) {
        closedAnnouncements.push(announcementId);
    }

    set_list_cookie(ANNOUNCEMENT_COOKIE, closedAnnouncements, 31);
}
