document.addEventListener("DOMContentLoaded", () => {
    // --- Elements ---
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const homeHeader = document.getElementById("home-header");
    const typingIndicator = document.getElementById("typing-indicator");
    
    // Vehicle Selection Elements
    const selectBikeCard = document.getElementById("select-bike-card");
    const selectCarCard = document.getElementById("select-car-card");
    const activeVehicleBadge = document.getElementById("active-vehicle-badge");
    const vehicleBadgeIcon = document.getElementById("vehicle-badge-icon");
    const vehicleBadgeText = document.getElementById("vehicle-badge-text");
    
    // Auth & User Elements
    const loginBtn = document.getElementById("login-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const userProfileBtn = document.getElementById("user-profile-btn");
    const headerUsername = document.getElementById("header-username");
    const authModal = document.getElementById("auth-modal");
    const closeModalBtn = document.getElementById("close-modal-btn");
    const authForm = document.getElementById("auth-form");
    const authSwitchLink = document.getElementById("auth-switch-link");
    const authSwitchText = document.getElementById("auth-switch-text");
    const modalTitle = document.getElementById("modal-title");
    const authSubmitBtn = document.getElementById("auth-submit-btn");
    const authEmailGroup = document.getElementById("auth-email-group");
    const authEmail = document.getElementById("auth-email");
    const authError = document.getElementById("auth-error");
    
    // History & Navigation
    const newChatBtn = document.getElementById("new-chat-btn");
    const historyContainer = document.getElementById("history-container");
    const historyList = document.getElementById("history-list");
    const searchHistory = document.getElementById("search-history");
    
    // Learning Mode Elements
    const openLearningBtn = document.getElementById("open-learning-btn");
    const quickLearnBtn = document.getElementById("quick-learn-btn");
    const learningModal = document.getElementById("learning-modal");
    const closeLearningBtn = document.getElementById("close-learning-btn");
    const learningTopicsGrid = document.getElementById("learning-topics-grid");
    
    // Delete Confirmation Modal Elements
    const deleteModal = document.getElementById("delete-modal");
    const closeDeleteBtn = document.getElementById("close-delete-btn");
    const cancelDeleteBtn = document.getElementById("cancel-delete-btn");
    const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
    
    // Settings Elements
    const settingsBtn = document.getElementById("settings-btn");
    const settingsModal = document.getElementById("settings-modal");
    const closeSettingsBtn = document.getElementById("close-settings-btn");
    const themeLight = document.getElementById("theme-light");
    const themeDark = document.getElementById("theme-dark");
    const settingsLangEn = document.getElementById("settings-lang-en");
    const settingsLangTa = document.getElementById("settings-lang-ta");
    const settingsUsernameDisplay = document.getElementById("settings-username-display");
    const settingsEmailDisplay = document.getElementById("settings-email-display");
    const settingsLogoutBtn = document.getElementById("settings-logout-btn");
    
    // Language Elements
    const langEnBtn = document.getElementById("lang-en");
    const langTaBtn = document.getElementById("lang-ta");
    
    // File & Voice Elements
    const fileUpload = document.getElementById("file-upload");
    const attachImgBtn = document.getElementById("attach-img-btn");
    const fileNameDisplay = document.getElementById("file-name-display");
    const fileNameText = document.getElementById("file-name-text");
    const removeFileBtn = document.getElementById("remove-file-btn");
    const voiceBtn = document.getElementById("voice-btn");
    const suggestionsPills = document.getElementById("suggestions-pills");

    // --- State Variables ---
    let token = localStorage.getItem("ai_moto_token") || localStorage.getItem("access_token");
    let username = localStorage.getItem("ai_moto_username") || localStorage.getItem("username");
    let userEmail = localStorage.getItem("ai_moto_email") || "";
    
    let currentVehicle = localStorage.getItem("ai_moto_vehicle") || "bike";
    let currentLanguage = localStorage.getItem("ai_moto_lang") || "English";
    let currentTheme = localStorage.getItem("ai_moto_theme") || "dark";
    let currentConversationId = null;
    let allConversations = [];
    let isLoginMode = true;
    let pendingDeleteConvId = null;
    let activeUtterance = null;
    let currentSpeakingBtn = null;
    let currentSpeakingText = null;

    // --- Suggestions Data ---
    const vehicleSuggestions = {
        bike: {
            English: [
                "Bike is not starting",
                "Strange engine clicking sound",
                "Front brake spongy feeling",
                "Chain loose and slipping",
                "Engine overheating quickly",
                "Battery getting discharged"
            ],
            Tamil: [
                "பைக் ஸ்டார்ட் ஆகவில்லை",
                "என்ஜினில் கிளிக் சத்தம்",
                "பிரேக் சரியாக பிடிக்கவில்லை",
                "செயின் தளர்வாக உள்ளது",
                "என்ஜின் அதிகமாக சூடாகிறது",
                "பேட்டரி சார்ஜ் இறங்குகிறது"
            ]
        },
        car: {
            English: [
                "Car AC not cooling properly",
                "Engine overheating in traffic",
                "Squeaking brake noise",
                "Battery warning light on",
                "Steering vibration at high speed",
                "Car cranks but won't start"
            ],
            Tamil: [
                "கார் ஏசி குளிர்ச்சியாக இல்லை",
                "என்ஜின் அதிகம் சூடாகிறது",
                "பிரேக்கில் விசித்திரமான சத்தம்",
                "பேட்டரி விளக்கு எரிகிறது",
                "ஸ்டீயரிங் அதிர்வு ஏற்படுகிறது",
                "கார் ஸ்டார்ட் ஆக மறுக்கிறது"
            ]
        }
    };

    // --- Learning Topics Data ---
    const learningTopics = {
        bike: [
            { icon: "fa-solid fa-gears", title: "Engine System", topic: "4-stroke and 2-stroke motorcycle engines" },
            { icon: "fa-solid fa-car-battery", title: "Battery & Charging", topic: "Bike 12V battery, alternator and charging system" },
            { icon: "fa-solid fa-circle-stop", title: "Braking System", topic: "Disc brakes, drum brakes, and ABS safety" },
            { icon: "fa-solid fa-arrows-split-up-and-left", title: "Clutch & Cable", topic: "Wet multi-plate clutch and clutch cable adjustment" },
            { icon: "fa-solid fa-link", title: "Gearbox & Chain", topic: "Sequential transmission, drive chain, and sprockets" },
            { icon: "fa-solid fa-ring", title: "Tyres & Pressure", topic: "Motorcycle tyres, tread wear, and correct PSI" },
            { icon: "fa-solid fa-arrows-up-down", title: "Suspension", topic: "Front telescopic forks and rear monoshock absorbers" },
            { icon: "fa-solid fa-snowflake", title: "Cooling System", topic: "Air cooling vs liquid cooling and radiators" },
            { icon: "fa-solid fa-bolt", title: "Electrical System", topic: "Spark plug, CDI/ECU, wiring, and fuses" },
            { icon: "fa-solid fa-gas-pump", title: "Fuel System", topic: "Carburetor vs Electronic Fuel Injection (EFI)" },
            { icon: "fa-solid fa-oil-can", title: "Periodic Maintenance", topic: "Engine oil change, filter replacement, and lube schedule" },
            { icon: "fa-solid fa-shield-halved", title: "Safety Systems", topic: "Combined Braking System (CBS) and Traction Control" }
        ],
        car: [
            { icon: "fa-solid fa-gears", title: "Car Engine", topic: "Internal combustion engine (Petrol, Diesel, Hybrid)" },
            { icon: "fa-solid fa-car-battery", title: "Battery & Alternator", topic: "Car starter battery, alternator, and electrical loads" },
            { icon: "fa-solid fa-circle-stop", title: "Brakes & ABS", topic: "Disc brakes, brake pads, ABS, and EBD" },
            { icon: "fa-solid fa-code-merge", title: "Transmission", topic: "Manual, Automatic (AT, CVT, DCT) gearboxes" },
            { icon: "fa-solid fa-fan", title: "Air Conditioning", topic: "Car AC compressor, condenser, refrigerant, and cabin filter" },
            { icon: "fa-solid fa-temperature-arrow-down", title: "Cooling System", topic: "Radiator, coolant, thermostat, and water pump" },
            { icon: "fa-solid fa-ring", title: "Tyres & Alignment", topic: "Car tyre pressure, wheel balancing, and wheel alignment" },
            { icon: "fa-solid fa-arrows-up-down", title: "Suspension & Struts", topic: "MacPherson struts, multi-link suspension, and bushings" },
            { icon: "fa-solid fa-microchip", title: "ECU & Sensors", topic: "Engine Control Unit, O2 sensors, and OBD diagnostics" },
            { icon: "fa-solid fa-gas-pump", title: "Fuel Injection", topic: "Fuel injectors, fuel pump, and fuel filter" },
            { icon: "fa-solid fa-oil-can", title: "Servicing Schedule", topic: "Engine oil change, brake fluid, coolant flush, and filters" },
            { icon: "fa-solid fa-shield-halved", title: "Safety & Airbags", topic: "Airbag system, crumple zones, and ADAS assistance" }
        ]
    };

    // --- Theme Logic ---
    function applyTheme(theme) {
        currentTheme = theme;
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
            themeLight.classList.add("active");
            themeDark.classList.remove("active");
        } else {
            document.documentElement.removeAttribute('data-theme');
            themeDark.classList.add("active");
            themeLight.classList.remove("active");
        }
        localStorage.setItem("ai_moto_theme", theme);
    }
    applyTheme(currentTheme);
    themeLight.addEventListener("click", () => applyTheme("light"));
    themeDark.addEventListener("click", () => applyTheme("dark"));

    // --- Language Logic ---
    function applyLanguage(lang) {
        currentLanguage = lang;
        localStorage.setItem("ai_moto_lang", lang);
        
        if (lang === 'English') {
            langEnBtn.classList.add("active");
            langTaBtn.classList.remove("active");
            settingsLangEn.classList.add("active");
            settingsLangTa.classList.remove("active");
            userInput.placeholder = currentVehicle === 'bike' 
                ? "Describe your bike problem or ask a question..." 
                : "Describe your car problem or ask a question...";
        } else {
            langTaBtn.classList.add("active");
            langEnBtn.classList.remove("active");
            settingsLangTa.classList.add("active");
            settingsLangEn.classList.remove("active");
            userInput.placeholder = currentVehicle === 'bike'
                ? "உங்கள் பைக் தொடர்பான கேள்வியை கேளுங்கள்..."
                : "உங்கள் கார் தொடர்பான கேள்வியை கேளுங்கள்...";
        }
        renderSuggestions();
    }

    langEnBtn.addEventListener("click", () => applyLanguage('English'));
    langTaBtn.addEventListener("click", () => applyLanguage('Tamil'));
    settingsLangEn.addEventListener("click", () => applyLanguage('English'));
    settingsLangTa.addEventListener("click", () => applyLanguage('Tamil'));

    // --- Vehicle Context Logic ---
    function setVehicle(vehicle, updateStorage = true) {
        currentVehicle = vehicle === 'car' ? 'car' : 'bike';
        if (updateStorage) {
            localStorage.setItem("ai_moto_vehicle", currentVehicle);
        }
        
        if (currentVehicle === 'bike') {
            vehicleBadgeIcon.textContent = "🏍️";
            vehicleBadgeText.textContent = "Bike Mode";
            activeVehicleBadge.style.borderColor = "rgba(0, 240, 255, 0.35)";
        } else {
            vehicleBadgeIcon.textContent = "🚗";
            vehicleBadgeText.textContent = "Car Mode";
            activeVehicleBadge.style.borderColor = "rgba(168, 85, 247, 0.4)";
        }
        
        applyLanguage(currentLanguage);
        renderLearningTopics();
    }

    selectBikeCard.addEventListener("click", () => {
        setVehicle("bike");
        homeHeader.style.display = "none";
        chatBox.classList.remove("hidden");
        userInput.focus();
    });

    selectCarCard.addEventListener("click", () => {
        setVehicle("car");
        homeHeader.style.display = "none";
        chatBox.classList.remove("hidden");
        userInput.focus();
    });

    // --- Suggestions Rendering ---
    function renderSuggestions() {
        suggestionsPills.innerHTML = "";
        const list = (vehicleSuggestions[currentVehicle] && vehicleSuggestions[currentVehicle][currentLanguage]) || vehicleSuggestions.bike.English;
        list.forEach(text => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "suggestion-pill";
            btn.innerHTML = `${text} <i class="fa-solid fa-chevron-right"></i>`;
            btn.addEventListener("click", () => {
                userInput.value = text;
                chatForm.dispatchEvent(new Event("submit"));
            });
            suggestionsPills.appendChild(btn);
        });
    }

    // --- Learning Mode Modal Logic ---
    function renderLearningTopics() {
        learningTopicsGrid.innerHTML = "";
        const topics = learningTopics[currentVehicle] || learningTopics.bike;
        topics.forEach(item => {
            const card = document.createElement("div");
            card.className = "learning-card";
            card.innerHTML = `<i class="${item.icon}"></i> <span>${item.title}</span>`;
            card.addEventListener("click", () => {
                learningModal.classList.add("hidden");
                homeHeader.style.display = "none";
                chatBox.classList.remove("hidden");
                
                const prompt = currentLanguage === 'Tamil'
                    ? `${currentVehicle === 'bike' ? 'பைக்' : 'கார்'} ${item.title} பற்றி விரிவாக விளக்குங்கள்.`
                    : `Explain how the ${currentVehicle} ${item.topic} works, common problems, and maintenance.`;
                
                submitMessage(prompt, null, "learn");
            });
            learningTopicsGrid.appendChild(card);
        });
    }

    function openLearningDialog() {
        renderLearningTopics();
        learningModal.classList.remove("hidden");
    }

    openLearningBtn.addEventListener("click", openLearningDialog);
    quickLearnBtn.addEventListener("click", openLearningDialog);
    closeLearningBtn.addEventListener("click", () => learningModal.classList.add("hidden"));

    // --- Auth Management ---
    function updateAuthUI() {
        if (token) {
            loginBtn.classList.add("hidden");
            logoutBtn.classList.remove("hidden");
            settingsLogoutBtn.classList.remove("hidden");
            headerUsername.textContent = username || "User";
            settingsUsernameDisplay.textContent = username || "User";
            settingsEmailDisplay.textContent = userEmail || "Logged in via 7-day session";
            loadConversations();
        } else {
            loginBtn.classList.remove("hidden");
            logoutBtn.classList.add("hidden");
            settingsLogoutBtn.classList.add("hidden");
            headerUsername.textContent = "Guest";
            settingsUsernameDisplay.textContent = "Guest";
            settingsEmailDisplay.textContent = "Not logged in";
            historyList.innerHTML = "<li style='padding: 8px 10px; color: var(--text-muted); font-size: 0.8rem;'>Log in to save conversations</li>";
        }
    }

    loginBtn.addEventListener("click", () => {
        isLoginMode = true;
        updateModalMode();
        authModal.classList.remove("hidden");
    });

    userProfileBtn.addEventListener("click", () => {
        if (!token) {
            authModal.classList.remove("hidden");
        } else {
            settingsModal.classList.remove("hidden");
        }
    });

    closeModalBtn.addEventListener("click", () => authModal.classList.add("hidden"));

    function logoutUser() {
        localStorage.removeItem("ai_moto_token");
        localStorage.removeItem("access_token");
        localStorage.removeItem("ai_moto_username");
        localStorage.removeItem("username");
        localStorage.removeItem("ai_moto_email");
        token = null;
        username = null;
        userEmail = "";
        currentConversationId = null;
        updateAuthUI();
        settingsModal.classList.add("hidden");
        resetToNewChat();
    }

    logoutBtn.addEventListener("click", logoutUser);
    settingsLogoutBtn.addEventListener("click", logoutUser);

    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");

    if (tabLogin && tabRegister) {
        tabLogin.addEventListener("click", () => {
            isLoginMode = true;
            updateModalMode();
        });
        tabRegister.addEventListener("click", () => {
            isLoginMode = false;
            updateModalMode();
        });
    }

    function updateModalMode() {
        if (tabLogin && tabRegister) {
            tabLogin.classList.toggle("active", isLoginMode);
            tabRegister.classList.toggle("active", !isLoginMode);
            tabLogin.setAttribute("aria-selected", isLoginMode);
            tabRegister.setAttribute("aria-selected", !isLoginMode);
        }

        modalTitle.innerHTML = isLoginMode 
            ? `<i class="fa-solid fa-user-lock"></i> Log In to AI MOTO` 
            : `<i class="fa-solid fa-user-plus"></i> Create Your AI MOTO ID`;
        authSubmitBtn.textContent = isLoginMode ? "Log In & Continue" : "Create ID & Start Chatting";
        authSwitchText.innerHTML = isLoginMode
            ? `New to AI MOTO? <a href="#" id="auth-switch-link">Create an account first</a>`
            : `Already have an ID? <a href="#" id="auth-switch-link">Switch to Log In</a>`;
        authEmailGroup.style.display = isLoginMode ? "none" : "block";
        authEmail.required = !isLoginMode;
        
        const authUsernameInput = document.getElementById("auth-username");
        if (authUsernameInput) {
            authUsernameInput.placeholder = isLoginMode ? "Enter username or email" : "Choose your username (e.g. Ragava-08)";
        }
        
        authError.classList.add("hidden");
        
        // Reattach switch link event
        const switchLink = document.getElementById("auth-switch-link");
        if (switchLink) {
            switchLink.addEventListener("click", (e) => {
                e.preventDefault();
                isLoginMode = !isLoginMode;
                updateModalMode();
            });
        }
    }

    authForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const uname = document.getElementById("auth-username").value.trim();
        const pwd = document.getElementById("auth-password").value;
        const email = authEmail.value.trim();
        
        const endpoint = isLoginMode ? "/api/login" : "/api/register";
        const payload = isLoginMode 
            ? { username: uname, password: pwd }
            : { username: uname, email: email, password: pwd };

        try {
            authSubmitBtn.disabled = true;
            authSubmitBtn.textContent = isLoginMode ? "Logging in..." : "Creating account...";

            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (res.ok && data.access_token) {
                // Instantly log in user (works for BOTH Login AND Registration!)
                token = data.access_token;
                username = data.username;
                userEmail = data.email || "";
                localStorage.setItem("ai_moto_token", token);
                localStorage.setItem("access_token", token);
                localStorage.setItem("ai_moto_username", username);
                localStorage.setItem("username", username);
                if (userEmail) localStorage.setItem("ai_moto_email", userEmail);
                authModal.classList.add("hidden");
                authForm.reset();
                updateAuthUI();
            } else if (res.ok) {
                // Fallback for registration without token
                isLoginMode = true;
                updateModalMode();
                authError.textContent = "Account created successfully! Click Log In now.";
                authError.style.color = "var(--success)";
                authError.classList.remove("hidden");
            } else {
                // If user doesn't exist during login, automatically guide them to Register!
                if (data.user_not_found) {
                    isLoginMode = false;
                    updateModalMode();
                    authError.textContent = `ID '${uname}' is not registered yet. Enter your email and click 'Create ID & Start Chatting'!`;
                    authError.style.color = "var(--accent)";
                    authError.classList.remove("hidden");
                    authEmail.focus();
                } else {
                    authError.textContent = data.message || "Authentication failed.";
                    authError.style.color = "var(--danger)";
                    authError.classList.remove("hidden");
                }
            }
        } catch (err) {
            authError.textContent = "Network error. Please check your connection.";
            authError.style.color = "var(--danger)";
            authError.classList.remove("hidden");
        } finally {
            authSubmitBtn.disabled = false;
            authSubmitBtn.textContent = isLoginMode ? "Log In & Continue" : "Create ID & Start Chatting";
        }
    });

    // --- Settings Dialog ---
    settingsBtn.addEventListener("click", () => settingsModal.classList.remove("hidden"));
    closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));

    // --- Conversations & History ---
    async function loadConversations(searchQuery = "") {
        if (!token) return;
        try {
            const url = searchQuery ? `/api/conversations?q=${encodeURIComponent(searchQuery)}` : "/api/conversations";
            const res = await fetch(url, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.status === 401 || res.status === 422) {
                logoutUser();
                return;
            }
            if (res.ok) {
                const data = await res.json();
                allConversations = data.conversations;
                renderHistory(allConversations);
            }
        } catch (e) {
            console.error("Failed to load chat history", e);
        }
    }

    function renderHistory(conversations) {
        historyList.innerHTML = "";
        if (!conversations || conversations.length === 0) {
            historyList.innerHTML = "<li style='padding: 8px 10px; color: var(--text-muted); font-size: 0.8rem;'>No conversations yet</li>";
            return;
        }

        conversations.forEach(conv => {
            const li = document.createElement("li");
            li.className = `history-item ${currentConversationId === conv.id ? 'active' : ''}`;
            
            const icon = conv.vehicle_type === 'car' ? '🚗' : '🏍️';
            
            const titleSpan = document.createElement("span");
            titleSpan.className = "history-item-title";
            titleSpan.innerHTML = `<span>${icon}</span> <span>${escapeHtml(conv.title)}</span>`;
            
            const delBtn = document.createElement("button");
            delBtn.type = "button";
            delBtn.className = "delete-chat-btn";
            delBtn.title = "Delete conversation";
            delBtn.innerHTML = '<i class="fa-regular fa-trash-can"></i>';
            delBtn.onclick = (e) => {
                e.stopPropagation();
                openDeleteDialog(conv.id, conv.title);
            };
            
            li.appendChild(titleSpan);
            li.appendChild(delBtn);
            
            li.onclick = () => loadSpecificConversation(conv.id);
            historyList.appendChild(li);
        });
    }

    if (searchHistory) {
        let debounceTimer = null;
        searchHistory.addEventListener("input", (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const val = e.target.value.trim().toLowerCase();
                const filtered = allConversations.filter(c => c.title.toLowerCase().includes(val));
                renderHistory(filtered);
            }, 150);
        });
    }

    async function loadSpecificConversation(id) {
        if (!token) return;
        try {
            const res = await fetch(`/api/conversations/${id}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                currentConversationId = id;
                
                // Set vehicle from conversation
                if (data.conversation && data.conversation.vehicle_type) {
                    setVehicle(data.conversation.vehicle_type, false);
                }
                
                chatBox.innerHTML = "";
                homeHeader.style.display = "none";
                chatBox.classList.remove("hidden");
                
                data.history.forEach(msg => {
                    appendMessage(msg.message, "user");
                    appendMessage(msg.response, "ai", msg.structured);
                });
                renderHistory(allConversations);
            }
        } catch (e) {
            console.error("Failed to load conversation", e);
        }
    }

    // --- Delete Confirmation Modal ---
    function openDeleteDialog(convId, title) {
        pendingDeleteConvId = convId;
        document.getElementById("delete-modal-text").textContent = `Are you sure you want to delete "${title || 'this conversation'}"?`;
        deleteModal.classList.remove("hidden");
    }

    closeDeleteBtn.addEventListener("click", () => deleteModal.classList.add("hidden"));
    cancelDeleteBtn.addEventListener("click", () => deleteModal.classList.add("hidden"));

    confirmDeleteBtn.addEventListener("click", async () => {
        if (!pendingDeleteConvId || !token) return;
        try {
            const res = await fetch(`/api/conversations/${pendingDeleteConvId}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const deletedId = pendingDeleteConvId;
                allConversations = allConversations.filter(c => c.id !== deletedId);
                deleteModal.classList.add("hidden");
                pendingDeleteConvId = null;
                
                if (currentConversationId === deletedId) {
                    resetToNewChat();
                } else {
                    renderHistory(allConversations);
                }
            }
        } catch (e) {
            console.error("Delete conversation error", e);
        }
    });

    // --- New Chat Reset ---
    function resetToNewChat() {
        stopSpeech();
        currentConversationId = null;
        chatBox.innerHTML = "";
        homeHeader.style.display = "flex";
        chatBox.classList.add("hidden");
        fileNameDisplay.classList.add("hidden");
        fileUpload.value = "";
        userInput.value = "";
        renderHistory(allConversations);
    }

    newChatBtn.addEventListener("click", resetToNewChat);

    // --- Voice Input Logic (Speech-to-Text) ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isRecording = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            userInput.focus();
        };

        recognition.onend = () => {
            isRecording = false;
            voiceBtn.classList.remove("recording");
            applyLanguage(currentLanguage);
        };

        recognition.onerror = (err) => {
            console.warn("Speech recognition error:", err);
            isRecording = false;
            voiceBtn.classList.remove("recording");
            applyLanguage(currentLanguage);
        };
    }

    voiceBtn.addEventListener("click", () => {
        if (!token) {
            authModal.classList.remove("hidden");
            return;
        }

        if (recognition) {
            if (!isRecording) {
                recognition.lang = currentLanguage === 'Tamil' ? 'ta-IN' : 'en-US';
                try {
                    recognition.start();
                    isRecording = true;
                    voiceBtn.classList.add("recording");
                    userInput.placeholder = currentLanguage === 'Tamil' ? "பேசவும் (Listening)..." : "Listening... Speak now";
                } catch (e) {
                    console.error("Could not start recognition", e);
                }
            } else {
                recognition.stop();
                isRecording = false;
                voiceBtn.classList.remove("recording");
            }
        } else {
            alert("Speech recognition is not supported in this browser. Please use text input.");
        }
    });

    // --- Text-to-Speech (TTS) Logic ---
    function stopSpeech() {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        if (currentSpeakingBtn) {
            currentSpeakingBtn.classList.remove("speaking");
            currentSpeakingBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
            currentSpeakingBtn = null;
        }
        activeUtterance = null;
        currentSpeakingText = null;
    }

    function toggleSpeak(text, btn) {
        if (!window.speechSynthesis) {
            alert("Text-to-speech is not supported by your browser.");
            return;
        }

        if (currentSpeakingBtn === btn) {
            stopSpeech();
            return;
        }

        stopSpeech();

        const cleanText = text
            .replace(/[#*_`~>-]/g, '')
            .replace(/\n+/g, ' ')
            .trim();

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = currentLanguage === 'Tamil' ? 'ta-IN' : 'en-US';
        utterance.rate = 0.95;

        btn.classList.add("speaking");
        btn.innerHTML = '<i class="fa-solid fa-circle-stop"></i> Stop';
        currentSpeakingBtn = btn;
        activeUtterance = utterance;
        currentSpeakingText = text;

        utterance.onend = () => {
            if (currentSpeakingBtn === btn) {
                btn.classList.remove("speaking");
                btn.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
                currentSpeakingBtn = null;
            }
        };

        utterance.onerror = (e) => {
            console.warn("TTS Error:", e);
            if (currentSpeakingBtn === btn) {
                btn.classList.remove("speaking");
                btn.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
                currentSpeakingBtn = null;
            }
        };

        window.speechSynthesis.speak(utterance);
    }

    // --- File Attachment Logic ---
    attachImgBtn.addEventListener("click", () => {
        fileUpload.click();
    });

    fileUpload.addEventListener("change", () => {
        if (fileUpload.files && fileUpload.files.length > 0) {
            const file = fileUpload.files[0];
            const sizeLimit = 5 * 1024 * 1024; // 5MB
            if (file.size > sizeLimit) {
                alert("Image size is too large. Please upload a smaller image (under 5MB).");
                fileUpload.value = "";
                fileNameDisplay.classList.add("hidden");
                return;
            }
            fileNameText.textContent = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            fileNameDisplay.classList.remove("hidden");
        } else {
            fileNameDisplay.classList.add("hidden");
        }
    });

    removeFileBtn.addEventListener("click", () => {
        fileUpload.value = "";
        fileNameDisplay.classList.add("hidden");
    });

    // --- Lightbox Image Preview Modal Handler ---
    const imageLightboxModal = document.getElementById("image-lightbox-modal");
    const closeLightboxBtn = document.getElementById("close-lightbox-btn");
    if (closeLightboxBtn) {
        closeLightboxBtn.addEventListener("click", () => imageLightboxModal.classList.add("hidden"));
    }
    if (imageLightboxModal) {
        imageLightboxModal.addEventListener("click", (e) => {
            if (e.target === imageLightboxModal) imageLightboxModal.classList.add("hidden");
        });
    }

    window.openImageModal = function(imgSrc, titleText, isVerified = true) {
        if (!imageLightboxModal) return;
        const imgEl = document.getElementById("lightbox-img");
        const titleEl = document.getElementById("lightbox-title");
        const badgeEl = document.getElementById("lightbox-badge");

        if (imgEl) imgEl.src = imgSrc;
        if (titleEl) titleEl.textContent = titleText || "Automotive Asset Preview";
        if (badgeEl) {
            badgeEl.innerHTML = isVerified !== false 
                ? '<i class="fa-solid fa-circle-check"></i> Verified Asset' 
                : '<i class="fa-solid fa-globe"></i> Visual Reference';
        }
        imageLightboxModal.classList.remove("hidden");
    };

    // --- Structured Output Rendering ---
    function buildStructuredCard(data) {
        if (!data || typeof data !== 'object') return null;

        const container = document.createElement("div");
        container.className = "structured-output-container";

        // 1. Computer Vision Detection Card
        if (data.vision_detection && data.vision_detection.detected) {
            const v = data.vision_detection;
            const visionCard = document.createElement("div");
            visionCard.className = "vision-detection-card";
            visionCard.innerHTML = `
                <div class="vision-card-header">
                    <div class="vision-card-title">
                        <i class="fa-solid fa-camera-retro"></i>
                        <span>AI Vision Detected: ${escapeHtml(v.part_name || v.part_class)}</span>
                    </div>
                    <span class="vision-confidence-pill">${v.confidence}% Confidence</span>
                </div>
                <div class="vision-confidence-bar-bg">
                    <div class="vision-confidence-bar-fill" style="width: ${Math.min(100, Math.max(10, v.confidence))}%;"></div>
                </div>
                <p class="vision-disclaimer"><i class="fa-solid fa-circle-info"></i> Assistive vision identification. Verify mechanical fitment and symptoms before servicing.</p>
            `;
            container.appendChild(visionCard);
        }

        // Determine expected vehicle type for this message
        const expectedVehicleType = (data.target_vehicle_type || data.vehicle_type || currentVehicle || 'bike').toLowerCase();
        const imageVehicleType = (data.image_vehicle_type || '').toLowerCase();

        // FRONTEND STRICT VALIDATION: If expected is bike, never allow a car image to be rendered!
        let isImageAllowed = true;
        let validationReason = "";
        if (data.image_url && imageVehicleType && imageVehicleType !== 'both') {
            if (expectedVehicleType === 'bike' && imageVehicleType === 'car') {
                isImageAllowed = false;
                validationReason = "Car image blocked: requested vehicle type is Bike.";
            } else if (expectedVehicleType === 'car' && imageVehicleType === 'bike') {
                isImageAllowed = false;
                validationReason = "Bike image blocked: requested vehicle type is Car.";
            }
        }

        // 2. Verified Media Hero Banner OR Placeholder Banner
        let mediaBannerHtml = "";
        if (data.image_url && isImageAllowed) {
            const isVerified = data.is_verified_image !== false;
            let badgeIcon = isVerified ? "fa-shield-halved" : "fa-globe";
            let badgeLabel = isVerified ? `Verified ${expectedVehicleType.toUpperCase()} Asset` : "Live Visual Reference";
            if (data.confidence && data.match_status === "exact_match") {
                badgeIcon = "fa-bullseye";
                badgeLabel = `Verified Exact Match (${data.confidence}%)`;
            }
            const imgTitle = data.image_name || data.title || "Vehicle / Component";

            mediaBannerHtml = `
                <div class="card-media-banner">
                    <div class="card-img-container" onclick="window.openImageModal('${data.image_url}', '${escapeHtml(imgTitle)}', ${isVerified})">
                        <img src="${data.image_url}" alt="${escapeHtml(imgTitle)}" class="card-featured-image" loading="lazy">
                        <div class="img-zoom-overlay"><i class="fa-solid fa-magnifying-glass-plus"></i> View Full Image</div>
                    </div>
                    <div class="card-media-meta">
                        <span class="card-verified-badge ${isVerified ? '' : 'web'}"><i class="fa-solid ${badgeIcon}"></i> ${badgeLabel}</span>
                        ${data.image_name ? `<span class="card-part-title-tag">${escapeHtml(data.image_name)}</span>` : ''}
                    </div>
                </div>
            `;
        } else if (data.is_placeholder || !isImageAllowed) {
            // Render Placeholder Banner
            const vIcon = expectedVehicleType === 'car' ? 'fa-car' : 'fa-motorcycle';
            const pTitle = data.placeholder_title || `Verified ${expectedVehicleType.toUpperCase()} Image Unavailable`;
            const pMsg = validationReason || data.placeholder_message || `A verified ${expectedVehicleType} image is not currently cataloged. Unrelated images are strictly blocked.`;

            mediaBannerHtml = `
                <div class="card-media-banner placeholder-banner">
                    <div class="placeholder-icon-wrap">
                        <i class="fa-solid ${vIcon}"></i>
                    </div>
                    <div class="placeholder-content">
                        <h4><i class="fa-solid fa-shield"></i> ${escapeHtml(pTitle)}</h4>
                        <p>${escapeHtml(pMsg)}</p>
                        <span class="placeholder-badge"><i class="fa-solid fa-check"></i> Strict Type Validation Active</span>
                    </div>
                </div>
            `;
        }

        // Handle pure placeholder card response
        if (data.response_type === "placeholder_info") {
            const pCard = document.createElement("div");
            pCard.className = "placeholder-card";
            pCard.innerHTML = mediaBannerHtml;
            container.appendChild(pCard);
            return container;
        }

        let priceEstimateHtml = "";
        if (data.price_estimate) {
            const p = data.price_estimate;
            const inrStr = typeof p === 'object' ? p.inr : p;
            const usdStr = typeof p === 'object' ? p.usd : null;
            const noteStr = typeof p === 'object' ? p.note : null;

            priceEstimateHtml = `
                <div class="card-price-estimate-box">
                    <div class="price-header">
                        <i class="fa-solid fa-tags"></i>
                        <span>Estimated Replacement Cost</span>
                    </div>
                    <div class="price-amounts">
                        <span class="price-inr">${escapeHtml(inrStr || '')}</span>
                        ${usdStr ? `<span class="price-usd">(${escapeHtml(usdStr)})</span>` : ''}
                    </div>
                    ${noteStr ? `<div class="price-note">${escapeHtml(noteStr)}</div>` : ''}
                </div>
            `;
        }

        // 3. Vehicle Overview Card (e.g. BMW M4 GT3 EVO, Yamaha R15)
        if (data.response_type === "vehicle_info" || (Array.isArray(data.specifications) && data.specifications.length > 0 && !data.components)) {
            const vCard = document.createElement("div");
            vCard.className = "vehicle-card";

            const title = data.title || "Vehicle Overview";
            const category = data.category || (data.manufacturer ? `${data.manufacturer} Vehicle` : "Automotive");
            const summary = data.summary || "";

            let specsHtml = "";
            if (Array.isArray(data.specifications) && data.specifications.length > 0) {
                specsHtml = `<div class="spec-grid">` + data.specifications.map(s => {
                    const iconClass = s.icon ? (s.icon.startsWith('fa-') ? `fa-solid ${s.icon}` : s.icon) : "fa-solid fa-gauge";
                    return `
                        <div class="spec-item">
                            <div class="spec-icon"><i class="${iconClass}"></i></div>
                            <div class="spec-info">
                                <span class="spec-label">${escapeHtml(s.label)}</span>
                                <span class="spec-value" title="${escapeHtml(s.value)}">${escapeHtml(s.value)}</span>
                            </div>
                        </div>
                    `;
                }).join("") + `</div>`;
            }

            let featuresHtml = "";
            if (Array.isArray(data.main_features) && data.main_features.length > 0) {
                featuresHtml = `
                    <div style="margin-top: 10px;">
                        <span style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted);">Key Equipment & Highlights:</span>
                        <div class="feature-pills-container">
                            ${data.main_features.map(f => `<span class="feature-pill"><i class="fa-solid fa-check" style="color: var(--accent);"></i> ${escapeHtml(f)}</span>`).join("")}
                        </div>
                    </div>
                `;
            }

            vCard.innerHTML = `
                ${mediaBannerHtml}
                <div class="vehicle-card-header">
                    <div class="vehicle-card-title-group">
                        <h3><i class="fa-solid fa-car-tunnel" style="color: var(--accent);"></i> ${escapeHtml(title)}</h3>
                    </div>
                    <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                        ${data.confidence ? `<span class="vehicle-category-badge" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.4); color: #10b981;"><i class="fa-solid fa-bullseye"></i> ${data.confidence}% Match</span>` : ''}
                        <span class="vehicle-category-badge"><i class="fa-solid fa-flag-checkered"></i> ${escapeHtml(category)}</span>
                    </div>
                </div>
                ${priceEstimateHtml}
                ${summary ? `<p class="vehicle-summary">${escapeHtml(summary)}</p>` : ""}
                ${specsHtml}
                ${featuresHtml}
            `;
            container.appendChild(vCard);
        }

        // 4. Diagnostic Result Card (Troubleshooting & Causes)
        if (data.response_type === "diagnostic_result" || data.possible_causes || data.recommended_checks) {
            const diagCard = document.createElement("div");
            diagCard.className = "diagnostic-card";

            const diagTitle = data.title || "Mechanical Diagnostics & Inspection";
            const probSummary = data.problem_summary || data.summary || "";

            let causesHtml = "";
            if (Array.isArray(data.possible_causes) && data.possible_causes.length > 0) {
                causesHtml = `
                    <div class="diag-subblock causes">
                        <div class="diag-subblock-title"><i class="fa-solid fa-triangle-exclamation"></i> Possible Causes</div>
                        <ul>${data.possible_causes.map(c => `<li>${escapeHtml(c)}</li>`).join("")}</ul>
                    </div>
                `;
            }

            let checksHtml = "";
            if (Array.isArray(data.recommended_checks) && data.recommended_checks.length > 0) {
                checksHtml = `
                    <div class="diag-subblock checks">
                        <div class="diag-subblock-title"><i class="fa-solid fa-screwdriver-wrench"></i> Recommended Checks</div>
                        <ul>${data.recommended_checks.map(k => `<li>${escapeHtml(k)}</li>`).join("")}</ul>
                    </div>
                `;
            }

            let actionHtml = "";
            if (data.suggested_action) {
                actionHtml = `
                    <div class="suggested-action-box">
                        <i class="fa-solid fa-wrench" style="color: var(--accent);"></i>
                        <div><strong>Suggested Action:</strong> ${escapeHtml(data.suggested_action)}</div>
                    </div>
                `;
            }

            diagCard.innerHTML = `
                ${mediaBannerHtml}
                <div class="diag-card-header">
                    <h3><i class="fa-solid fa-stethoscope" style="color: var(--accent);"></i> ${escapeHtml(diagTitle)}</h3>
                </div>
                ${priceEstimateHtml}
                ${probSummary ? `<p class="diag-summary">${escapeHtml(probSummary)}</p>` : ""}
                <div class="diag-grid">${causesHtml}${checksHtml}</div>
                ${actionHtml}
            `;
            container.appendChild(diagCard);
        }

        // 5. Vehicle Parts & Component Cards
        if (Array.isArray(data.components) && data.components.length > 0) {
            const partsContainer = document.createElement("div");
            partsContainer.className = "parts-container";

            data.components.forEach(c => {
                const pCard = document.createElement("div");
                pCard.className = "part-card";

                const cName = c.name || "Component";
                const cCat = c.category || "Vehicle System";
                const cPurpose = c.purpose || c.description || "";
                const cWorking = c.working || "";

                // Component Thumbnail and Price
                let compMediaHtml = "";
                if (c.image_url) {
                    compMediaHtml = `
                        <div class="part-media-row">
                            <div class="part-thumb-wrap" onclick="window.openImageModal('${c.image_url}', '${escapeHtml(cName)}')">
                                <img src="${c.image_url}" alt="${escapeHtml(cName)}" class="part-thumb-img" loading="lazy">
                                <span class="part-zoom-hint"><i class="fa-solid fa-expand"></i></span>
                            </div>
                            <div class="part-meta-info">
                                <span class="verified-part-tag"><i class="fa-solid fa-circle-check"></i> Verified Component</span>
                                ${c.price_estimate ? `<span class="part-price-badge"><i class="fa-solid fa-tag"></i> Est: ${escapeHtml(c.price_estimate.inr || c.price_estimate)}</span>` : ''}
                            </div>
                        </div>
                    `;
                }

                let symptomsHtml = "";
                if (Array.isArray(c.symptoms) && c.symptoms.length > 0) {
                    symptomsHtml = `
                        <div class="part-subblock">
                            <div class="part-subblock-title"><i class="fa-solid fa-triangle-exclamation" style="color: #f59e0b;"></i> Common Symptoms</div>
                            <ul>${c.symptoms.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
                        </div>
                    `;
                }

                let checksHtml = "";
                if (Array.isArray(c.checks) && c.checks.length > 0) {
                    checksHtml = `
                        <div class="part-subblock">
                            <div class="part-subblock-title"><i class="fa-solid fa-screwdriver-wrench" style="color: var(--accent);"></i> Recommended Checks</div>
                            <ul>${c.checks.map(k => `<li>${escapeHtml(k)}</li>`).join("")}</ul>
                        </div>
                    `;
                }

                let subGridHtml = "";
                if (symptomsHtml || checksHtml) {
                    subGridHtml = `<div class="part-details-grid">${symptomsHtml}${checksHtml}</div>`;
                }

                let maintHtml = "";
                if (c.maintenance) {
                    maintHtml = `<p style="font-size: 0.83rem; color: var(--text-secondary); margin-top: 6px;"><strong>Maintenance Tip:</strong> ${escapeHtml(c.maintenance)}</p>`;
                }

                let safetyHtml = "";
                if (c.safety_warning) {
                    safetyHtml = `
                        <div class="safety-alert-banner" style="margin-top: 8px;">
                            <i class="fa-solid fa-shield-halved"></i>
                            <div>${escapeHtml(c.safety_warning)}</div>
                        </div>
                    `;
                }

                pCard.innerHTML = `
                    <div class="part-card-header">
                        <span class="part-title"><i class="fa-solid fa-gears" style="color: var(--accent);"></i> ${escapeHtml(cName)}</span>
                        <span class="part-system-tag">${escapeHtml(cCat)}</span>
                    </div>
                    ${compMediaHtml}
                    ${cPurpose ? `<p class="part-purpose"><strong>Purpose:</strong> ${escapeHtml(cPurpose)}</p>` : ""}
                    ${cWorking ? `<p class="part-purpose" style="font-size: 0.85rem; color: var(--text-muted);"><strong>Working:</strong> ${escapeHtml(cWorking)}</p>` : ""}
                    ${subGridHtml}
                    ${maintHtml}
                    ${safetyHtml}
                `;
                partsContainer.appendChild(pCard);
            });

            container.appendChild(partsContainer);
        }

        // 6. Global Safety Warning Banner
        if (data.safety_warning && (!data.components || data.components.length === 0 || !data.components.some(c => c.safety_warning === data.safety_warning))) {
            const safetyBanner = document.createElement("div");
            safetyBanner.className = "safety-alert-banner";
            safetyBanner.innerHTML = `
                <i class="fa-solid fa-shield-halved"></i>
                <div><strong>Safety Guidance:</strong> ${escapeHtml(data.safety_warning)}</div>
            `;
            container.appendChild(safetyBanner);
        }

        // 7. Interactive Related Questions Chips
        if (Array.isArray(data.related_questions) && data.related_questions.length > 0) {
            const relGroup = document.createElement("div");
            relGroup.className = "related-questions-group";
            relGroup.innerHTML = `<span class="related-questions-title"><i class="fa-regular fa-compass"></i> Explore Related Questions:</span>`;

            const chipsList = document.createElement("div");
            chipsList.className = "related-chips-list";

            data.related_questions.forEach(q => {
                const chip = document.createElement("button");
                chip.type = "button";
                chip.className = "related-chip-btn";
                chip.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> ${escapeHtml(q)}`;
                chip.onclick = () => {
                    userInput.value = q;
                    submitMessage(q, null, "chat");
                };
                chipsList.appendChild(chip);
            });

            relGroup.appendChild(chipsList);
            container.appendChild(relGroup);
        }

        return container;
    }

    // --- Message Rendering ---
    function appendMessage(content, sender = "user", structuredData = null) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender === 'user' ? 'user-message' : 'ai-message'}`;
        
        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        
        if (sender === "ai") {
            let parsedStructured = structuredData;
            let displayText = content;

            // If structuredData not passed explicitly, attempt extraction from text delimiter
            if (!parsedStructured && typeof content === 'string') {
                const delimPattern = /<<<STRUCTURED_JSON>>>([\s\S]*?)<<<END_STRUCTURED_JSON>>>/g;
                const match = delimPattern.exec(content);
                if (match) {
                    try {
                        parsedStructured = JSON.parse(match[1].trim());
                        displayText = content.replace(delimPattern, '').trim();
                    } catch (e) {
                        console.warn("Client JSON parse fallback", e);
                    }
                }
            }

            const renderedMarkdown = window.marked ? marked.parse(displayText || "") : escapeHtml(displayText || "");
            contentDiv.innerHTML = renderedMarkdown;

            // Render structured cards if present
            if (parsedStructured) {
                const cardEl = buildStructuredCard(parsedStructured);
                if (cardEl) {
                    contentDiv.appendChild(cardEl);
                }
            }

            // Add Listen (TTS) button
            const actionsDiv = document.createElement("div");
            actionsDiv.className = "message-actions";
            
            const speakBtn = document.createElement("button");
            speakBtn.type = "button";
            speakBtn.className = "speak-btn";
            speakBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i> Listen';
            speakBtn.onclick = () => toggleSpeak(displayText || content, speakBtn);
            
            actionsDiv.appendChild(speakBtn);
            contentDiv.appendChild(actionsDiv);
        } else {
            contentDiv.textContent = content;
        }
        
        msgDiv.appendChild(contentDiv);
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // --- Message Submission ---
    async function submitMessage(messageText, fileObj = null, mode = "chat") {
        if (!token) {
            authModal.classList.remove("hidden");
            return;
        }

        const trimmed = messageText.trim();
        if (!trimmed && !fileObj) return;

        // Reveal chat box
        homeHeader.style.display = "none";
        chatBox.classList.remove("hidden");

        let displayMsg = trimmed;
        if (fileObj) {
            displayMsg = `[Attached: ${fileObj.name}]\n${displayMsg}`.trim();
        }

        appendMessage(displayMsg, "user");
        
        // Reset inputs
        userInput.value = "";
        fileUpload.value = "";
        fileNameDisplay.classList.add("hidden");
        
        // Show typing indicator
        typingIndicator.classList.remove("hidden");
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const formData = new FormData();
            formData.append("message", trimmed);
            formData.append("vehicle_type", currentVehicle);
            formData.append("language", currentLanguage);
            formData.append("mode", mode);
            if (currentConversationId) {
                formData.append("conversation_id", currentConversationId);
            }
            if (fileObj) {
                formData.append("file", fileObj);
            }

            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            const data = await response.json();
            typingIndicator.classList.add("hidden");

            if (response.ok) {
                if (data.conversation_id) {
                    currentConversationId = data.conversation_id;
                }
                appendMessage(data.response, "ai", data.structured);
                loadConversations();
            } else if (response.status === 401 || response.status === 422) {
                logoutUser();
                alert("Your session expired. Please log in again.");
                authModal.classList.remove("hidden");
            } else {
                appendMessage(data.message || "I encountered an error processing your request.", "ai");
            }
        } catch (err) {
            typingIndicator.classList.add("hidden");
            console.error("Chat error:", err);
            appendMessage("Unable to connect to AI MOTO server. Please check your internet connection.", "ai");
        }
    }

    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = userInput.value;
        const file = (fileUpload.files && fileUpload.files[0]) || null;
        submitMessage(text, file, "chat");
    });

    // --- Quick Prompt Buttons (Hero) ---
    document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            if (query) {
                if (query.toLowerCase().includes("car") || query.toLowerCase().includes("bmw")) {
                    setVehicle("car", true);
                } else if (query.toLowerCase().includes("bike")) {
                    setVehicle("bike", true);
                }
                userInput.value = query;
                submitMessage(query, null, "chat");
            }
        });
    });

    // --- Initial Setup ---
    setVehicle(currentVehicle);
    updateAuthUI();
});
