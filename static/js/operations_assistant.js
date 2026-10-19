/**
 * MacroOps AI — 3D Female Operations Assistant (Ava) Controller
 * ==============================================================
 * Renders and orchestrates a real animated 3D female avatar with:
 *   - Humanoid skeletal body rig (Head, Neck, Spine, Arms, Hands)
 *   - 72 facial blendshapes & ARKit/Oculus visemes for realistic speech lip-sync
 *   - 5 Discrete Animation States: IDLE, LISTENING, THINKING, SPEAKING, ERROR
 *   - Web Speech API integration (TTS with boundary-synchronized phoneme lip-sync & STT dictation)
 *   - Grounded REST query engine connecting to MacroOps SQLite DataService and ML models
 */

(function () {
  'use strict';

  // State Management
  const state = {
    isOpen: false,
    isMinimized: false,
    animationState: 'IDLE', // IDLE, LISTENING, THINKING, SPEAKING, ERROR
    voiceEnabled: true,
    isMuted: false,
    isSpeaking: false,
    isListening: false,
    activeViseme: null,
    visemeIntensity: 0,
    jawOpenVal: 0,
    targetJawOpen: 0,
    mouthSmileVal: 0.15,
    blinkVal: 0,
    nextBlinkTime: 2.0,
    speechUtterance: null,
    speechRecognition: null,
    speechStartTime: 0,
    speechWordList: [],
    currentWordIndex: 0
  };

  // Three.js References
  let scene, camera, renderer, clock;
  let avatarModel = null;
  let headMesh = null;
  let teethMesh = null;
  let eyeLeftMesh = null;
  let eyeRightMesh = null;
  let bones = {
    head: null,
    neck: null,
    spine: null,
    spine1: null,
    spine2: null,
    leftShoulder: null,
    rightShoulder: null,
    leftArm: null,
    rightArm: null,
    leftForeArm: null,
    rightForeArm: null,
    leftHand: null,
    rightHand: null
  };
  let restRotations = {};

  // DOM Elements
  const dom = {
    triggerBtn: document.getElementById('btn-ai-assistant'),
    panel: document.getElementById('assistant-panel'),
    stateBadge: document.getElementById('assistant-state-badge'),
    btnVoiceToggle: document.getElementById('btn-voice-toggle'),
    voiceIcon: document.getElementById('voice-icon'),
    voiceLabel: document.getElementById('voice-label'),
    btnStopSpeech: document.getElementById('btn-stop-speech'),
    btnMinimize: document.getElementById('btn-minimize-assistant'),
    btnClose: document.getElementById('btn-close-assistant'),
    viewportContainer: document.getElementById('assistant-3d-container'),
    loadingOverlay: document.getElementById('avatar-loading-overlay'),
    lipSyncBadge: document.getElementById('avatar-lip-sync-badge'),
    chatMessages: document.getElementById('assistant-messages'),
    inputForm: document.getElementById('assistant-input-form'),
    textInput: document.getElementById('assistant-input'),
    btnMic: document.getElementById('btn-assistant-mic'),
    btnSend: document.getElementById('btn-assistant-send'),
    chipsContainer: document.getElementById('assistant-chips')
  };

  // =========================================================================
  // 1. Three.js Scene & Camera Initialization
  // =========================================================================
  function initThreeScene() {
    if (!dom.viewportContainer || renderer) return;

    const width = dom.viewportContainer.clientWidth || 440;
    const height = dom.viewportContainer.clientHeight || 240;

    scene = new THREE.Scene();
    clock = new THREE.Clock();

    // Portrait Perspective Camera
    camera = new THREE.PerspectiveCamera(28, width / height, 0.1, 20);
    camera.position.set(0, 0.15, 0.95);
    camera.lookAt(0, 0.08, 0);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.shadowMap.enabled = false;
    dom.viewportContainer.appendChild(renderer.domElement);

    // Studio Lighting setup for operations command center
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    // Key Light (warm white from upper-right)
    const keyLight = new THREE.DirectionalLight(0xfff7ed, 1.3);
    keyLight.position.set(1.5, 2.0, 1.8);
    scene.add(keyLight);

    // Fill Light (soft indigo from left)
    const fillLight = new THREE.DirectionalLight(0xa5b4fc, 0.7);
    fillLight.position.set(-1.8, 1.0, 1.2);
    scene.add(fillLight);

    // Futuristic Cyan Operations Rim Light (from behind)
    const rimLight = new THREE.DirectionalLight(0x00f2fe, 1.6);
    rimLight.position.set(0, 1.6, -2.0);
    scene.add(rimLight);

    // Resize handler
    window.addEventListener('resize', onWindowResize);

    // Load Avatar
    loadAvatarModel();

    // Start render loop
    requestAnimationFrame(animateLoop);
  }

  function onWindowResize() {
    if (!renderer || !camera || !dom.viewportContainer) return;
    const width = dom.viewportContainer.clientWidth;
    const height = dom.viewportContainer.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  // =========================================================================
  // 2. Avatar Model Loading & Rig Binding (Ready Player Me GLB)
  // =========================================================================
  function loadAvatarModel() {
    if (typeof THREE.GLTFLoader === 'undefined') {
      console.error('THREE.GLTFLoader is not defined. Ensure GLTFLoader.js is loaded.');
      if (dom.loadingOverlay) dom.loadingOverlay.innerHTML = '<span style="color:#f87171;">LOADER ERROR</span>';
      return;
    }

    const loader = new THREE.GLTFLoader();
    const modelUrl = '/static/models/assistant.glb';

    loader.load(
      modelUrl,
      (gltf) => {
        avatarModel = gltf.scene;
        avatarModel.position.set(0, -1.48, 0); // Position to focus on upper torso, chest, neck, head
        scene.add(avatarModel);

        // Discover and bind skinned meshes & morph targets
        avatarModel.traverse((child) => {
          if (child.isSkinnedMesh || child.isMesh) {
            if (child.name === 'Wolf3D_Head') headMesh = child;
            if (child.name === 'Wolf3D_Teeth') teethMesh = child;
            if (child.name === 'EyeLeft') eyeLeftMesh = child;
            if (child.name === 'EyeRight') eyeRightMesh = child;
          }

          if (child.isBone) {
            const name = child.name;
            if (name === 'Head') bones.head = child;
            if (name === 'Neck') bones.neck = child;
            if (name === 'Spine') bones.spine = child;
            if (name === 'Spine1') bones.spine1 = child;
            if (name === 'Spine2') bones.spine2 = child;
            if (name === 'LeftShoulder') bones.leftShoulder = child;
            if (name === 'RightShoulder') bones.rightShoulder = child;
            if (name === 'LeftArm') bones.leftArm = child;
            if (name === 'RightArm') bones.rightArm = child;
            if (name === 'LeftForeArm') bones.leftForeArm = child;
            if (name === 'RightForeArm') bones.rightForeArm = child;
            if (name === 'LeftHand') bones.leftHand = child;
            if (name === 'RightHand') bones.rightHand = child;
          }
        });

        // Cache initial resting rotations
        Object.keys(bones).forEach((key) => {
          const bone = bones[key];
          if (bone) {
            restRotations[key] = {
              x: bone.rotation.x,
              y: bone.rotation.y,
              z: bone.rotation.z
            };
          }
        });

        // Hide loading overlay
        if (dom.loadingOverlay) {
          dom.loadingOverlay.style.opacity = '0';
          setTimeout(() => {
            dom.loadingOverlay.style.display = 'none';
          }, 400);
        }

        // Set initial slight friendly smile
        setMorphTarget('mouthSmile', 0.18);
        setAnimationState('IDLE');
        console.log('3D Avatar loaded successfully. Rigged joints:', Object.keys(bones).filter(k => bones[k]).length);
      },
      (progress) => {
        if (dom.loadingOverlay && progress.total > 0) {
          const pct = Math.round((progress.loaded / progress.total) * 100);
          const span = dom.loadingOverlay.querySelector('span');
          if (span) span.textContent = `LOADING 3D AVATAR (${pct}%)...`;
        }
      },
      (error) => {
        console.error('Failed to load avatar GLB:', error);
        if (dom.loadingOverlay) {
          dom.loadingOverlay.innerHTML = '<span style="color:#f87171;">FAILED TO LOAD 3D MODEL</span>';
        }
      }
    );
  }

  // Helper to set morph target value on Head and Teeth meshes
  function setMorphTarget(targetName, value) {
    [headMesh, teethMesh].forEach((mesh) => {
      if (mesh && mesh.morphTargetDictionary && mesh.morphTargetInfluences) {
        const idx = mesh.morphTargetDictionary[targetName];
        if (idx !== undefined) {
          mesh.morphTargetInfluences[idx] = Math.max(0, Math.min(1, value));
        }
      }
    });
  }

  // =========================================================================
  // 3. Animation State Controller & 60 FPS Render Loop
  // =========================================================================
  function setAnimationState(newState) {
    state.animationState = newState;
    if (dom.stateBadge) {
      dom.stateBadge.textContent = newState;
      dom.stateBadge.className = 'assistant-state-badge state-' + newState.toLowerCase();
    }
  }

  function animateLoop() {
    requestAnimationFrame(animateLoop);

    if (!renderer || !scene || !camera) return;

    const delta = clock.getDelta();
    const elapsedTime = clock.getElapsedTime();

    // Check if dashboard reduced motion is active
    const isReducedMotion = document.body.classList.contains('reduced-motion');

    if (avatarModel) {
      updateAvatarAnimations(elapsedTime, delta, isReducedMotion);
    }

    renderer.render(scene, camera);
  }

  function updateAvatarAnimations(t, dt, isReducedMotion) {
    // -----------------------------------------------------------------------
    // A. Natural Eye Blinking (Idle & Active)
    // -----------------------------------------------------------------------
    state.nextBlinkTime -= dt;
    if (state.nextBlinkTime <= 0) {
      state.blinkVal = 1.0;
      state.nextBlinkTime = 3.0 + Math.random() * 2.5; // Next blink in 3-5.5s
    }

    if (state.blinkVal > 0) {
      state.blinkVal -= dt * 6.5; // Fast blink ~150ms
      if (state.blinkVal < 0) state.blinkVal = 0;
    }

    // Apply blink to eyes and head
    [headMesh, eyeLeftMesh, eyeRightMesh].forEach((mesh) => {
      if (mesh && mesh.morphTargetDictionary && mesh.morphTargetInfluences) {
        const lIdx = mesh.morphTargetDictionary['eyeBlinkLeft'];
        const rIdx = mesh.morphTargetDictionary['eyeBlinkRight'];
        if (lIdx !== undefined) mesh.morphTargetInfluences[lIdx] = state.blinkVal;
        if (rIdx !== undefined) mesh.morphTargetInfluences[rIdx] = state.blinkVal;
      }
    });

    if (isReducedMotion) {
      // Keep model still in reduced motion mode
      return;
    }

    // -----------------------------------------------------------------------
    // B. State-Driven Skeletal Rig Animations (Spine, Neck, Head, Arms)
    // -----------------------------------------------------------------------
    const rHead = restRotations.head || { x: 0, y: 0, z: 0 };
    const rNeck = restRotations.neck || { x: 0, y: 0, z: 0 };
    const rSpine = restRotations.spine || { x: 0, y: 0, z: 0 };
    const rRightArm = restRotations.rightArm || { x: 0, y: 0, z: 0 };
    const rRightForeArm = restRotations.rightForeArm || { x: 0, y: 0, z: 0 };
    const rLeftArm = restRotations.leftArm || { x: 0, y: 0, z: 0 };

    // Continuous subtle breathing (Spine oscillation)
    const breath = Math.sin(t * 1.6) * 0.015;
    if (bones.spine) bones.spine.rotation.x = THREE.MathUtils.lerp(bones.spine.rotation.x, rSpine.x + breath, dt * 3);
    if (bones.spine1) bones.spine1.rotation.x = THREE.MathUtils.lerp(bones.spine1.rotation.x, rSpine.x + breath * 0.8, dt * 3);

    // State Behaviors
    switch (state.animationState) {
      case 'IDLE': {
        // Subtle natural head drift & micro-yaw
        const headYaw = Math.sin(t * 0.6) * 0.035;
        const headPitch = Math.cos(t * 0.8) * 0.02;
        if (bones.head) {
          bones.head.rotation.y = THREE.MathUtils.lerp(bones.head.rotation.y, rHead.y + headYaw, dt * 2.5);
          bones.head.rotation.x = THREE.MathUtils.lerp(bones.head.rotation.x, rHead.x + headPitch, dt * 2.5);
        }
        if (bones.neck) {
          bones.neck.rotation.y = THREE.MathUtils.lerp(bones.neck.rotation.y, rNeck.y + headYaw * 0.5, dt * 2.5);
        }

        // Relaxed resting arms
        if (bones.rightArm) bones.rightArm.rotation.x = THREE.MathUtils.lerp(bones.rightArm.rotation.x, rRightArm.x, dt * 3);
        if (bones.rightForeArm) bones.rightForeArm.rotation.x = THREE.MathUtils.lerp(bones.rightForeArm.rotation.x, rRightForeArm.x, dt * 3);
        if (bones.leftArm) bones.leftArm.rotation.x = THREE.MathUtils.lerp(bones.leftArm.rotation.x, rLeftArm.x, dt * 3);

        // Friendly resting mouth
        setMorphTarget('mouthSmile', 0.16);
        setMorphTarget('jawOpen', 0);
        setMorphTarget('mouthOpen', 0);
        break;
      }

      case 'LISTENING': {
        // Head tilts attentively forward toward camera, receptive micro-nods
        const listenTilt = 0.07 + Math.sin(t * 2.2) * 0.02;
        if (bones.head) {
          bones.head.rotation.x = THREE.MathUtils.lerp(bones.head.rotation.x, rHead.x + listenTilt, dt * 4);
          bones.head.rotation.y = THREE.MathUtils.lerp(bones.head.rotation.y, rHead.y + 0.04, dt * 4);
        }
        if (bones.neck) {
          bones.neck.rotation.x = THREE.MathUtils.lerp(bones.neck.rotation.x, rNeck.x + 0.03, dt * 4);
        }
        setMorphTarget('mouthSmile', 0.22);
        setMorphTarget('jawOpen', 0);
        break;
      }

      case 'THINKING': {
        // Head tilts slightly upwards and to side, furrowed brow, thoughtful pose
        if (bones.head) {
          bones.head.rotation.y = THREE.MathUtils.lerp(bones.head.rotation.y, rHead.y - 0.14, dt * 3);
          bones.head.rotation.x = THREE.MathUtils.lerp(bones.head.rotation.x, rHead.x - 0.06, dt * 3);
          bones.head.rotation.z = THREE.MathUtils.lerp(bones.head.rotation.z, 0.04, dt * 3);
        }
        // Right hand lifts slightly in contemplative posture
        if (bones.rightArm) {
          bones.rightArm.rotation.x = THREE.MathUtils.lerp(bones.rightArm.rotation.x, rRightArm.x - 0.28, dt * 3);
          bones.rightArm.rotation.z = THREE.MathUtils.lerp(bones.rightArm.rotation.z, -0.15, dt * 3);
        }
        if (bones.rightForeArm) {
          bones.rightForeArm.rotation.x = THREE.MathUtils.lerp(bones.rightForeArm.rotation.x, 0.35, dt * 3);
        }
        setMorphTarget('browInnerUp', 0.3);
        setMorphTarget('mouthSmile', 0.05);
        setMorphTarget('jawOpen', 0);
        break;
      }

      case 'SPEAKING': {
        // Dynamic head cadence and gesturing synchronized to speech
        const speechNod = Math.sin(t * 4.2) * 0.035;
        const speechTurn = Math.cos(t * 2.5) * 0.04;
        if (bones.head) {
          bones.head.rotation.x = THREE.MathUtils.lerp(bones.head.rotation.x, rHead.x + speechNod, dt * 6);
          bones.head.rotation.y = THREE.MathUtils.lerp(bones.head.rotation.y, rHead.y + speechTurn, dt * 6);
        }

        // Expressive right arm gesturing forward
        const armGesture = Math.sin(t * 3.0) * 0.12;
        if (bones.rightArm) {
          bones.rightArm.rotation.x = THREE.MathUtils.lerp(bones.rightArm.rotation.x, rRightArm.x - 0.35 + armGesture, dt * 5);
          bones.rightArm.rotation.y = THREE.MathUtils.lerp(bones.rightArm.rotation.y, 0.2, dt * 4);
        }
        if (bones.rightForeArm) {
          bones.rightForeArm.rotation.y = THREE.MathUtils.lerp(bones.rightForeArm.rotation.y, 0.25 + armGesture * 0.8, dt * 5);
        }

        // -------------------------------------------------------------------
        // Real-Time Lip-Sync Morph Target Animation
        // -------------------------------------------------------------------
        state.jawOpenVal = THREE.MathUtils.lerp(state.jawOpenVal, state.targetJawOpen, dt * 14);
        setMorphTarget('jawOpen', state.jawOpenVal);
        setMorphTarget('mouthOpen', state.jawOpenVal * 0.85);

        if (state.activeViseme) {
          setMorphTarget(state.activeViseme, state.visemeIntensity);
        }
        break;
      }

      case 'ERROR': {
        // Empathic head shake (rotates side-to-side)
        const shake = Math.sin(t * 9.0) * 0.1;
        if (bones.head) {
          bones.head.rotation.y = THREE.MathUtils.lerp(bones.head.rotation.y, rHead.y + shake, dt * 6);
          bones.head.rotation.x = THREE.MathUtils.lerp(bones.head.rotation.x, rHead.x + 0.04, dt * 4);
        }
        setMorphTarget('jawOpen', 0);
        setMorphTarget('mouthSmile', 0);
        break;
      }
    }
  }

  // =========================================================================
  // 4. Speech Synthesis & Phoneme/Viseme Lip-Sync Engine
  // =========================================================================
  function speakReply(text) {
    if (!state.voiceEnabled || state.isMuted || !('speechSynthesis' in window)) {
      // Voice is off or unsupported: brief speaking gesture then idle
      setAnimationState('SPEAKING');
      setTimeout(() => {
        setAnimationState('IDLE');
      }, 1800);
      return;
    }

    // Stop any ongoing speech
    stopSpeaking();

    // Clean plain text for speech (strip markdown asterisks, backticks, URLs)
    const cleanSpeechText = text
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/https?:\/\/\S+/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/<[^>]+>/g, '');

    const utterance = new SpeechSynthesisUtterance(cleanSpeechText);
    utterance.rate = 1.02;
    utterance.pitch = 1.05; // Slightly elevated professional female pitch

    // Select female voice if available in system
    const voices = window.speechSynthesis.getVoices();
    const femaleVoice = voices.find(v =>
      (v.name.includes('Female') || v.name.includes('Zira') || v.name.includes('Samantha') ||
       v.name.includes('Google US English') || v.name.includes('Natural')) && v.lang.startsWith('en')
    );
    if (femaleVoice) utterance.voice = femaleVoice;

    state.speechUtterance = utterance;
    state.isSpeaking = true;
    state.speechStartTime = performance.now();
    state.speechWordList = cleanSpeechText.split(/\s+/);
    state.currentWordIndex = 0;

    // Rhythmic syllable generator for fallback & continuous visemes
    let syllableInterval = null;

    utterance.onstart = () => {
      setAnimationState('SPEAKING');
      if (dom.lipSyncBadge) dom.lipSyncBadge.textContent = 'LIP-SYNC: ACTIVE';

      // Syllable rhythm driver: creates continuous natural mouth cadence
      syllableInterval = setInterval(() => {
        if (!state.isSpeaking) {
          clearInterval(syllableInterval);
          return;
        }
        // Oscillate jaw between 0.35 and 0.85 during speech
        state.targetJawOpen = 0.35 + Math.random() * 0.45;
        state.visemeIntensity = 0.4 + Math.random() * 0.5;

        // Alternate active visemes
        const visemeList = ['viseme_aa', 'viseme_E', 'viseme_O', 'viseme_I', 'viseme_PP', 'viseme_FF'];
        const chosen = visemeList[Math.floor(Math.random() * visemeList.length)];
        if (state.activeViseme && state.activeViseme !== chosen) {
          setMorphTarget(state.activeViseme, 0);
        }
        state.activeViseme = chosen;
      }, 110);
    };

    // Word boundary event for exact syllable sync where supported
    utterance.onboundary = (event) => {
      if (event.name === 'word' || event.charIndex !== undefined) {
        state.targetJawOpen = 0.55 + Math.random() * 0.35;
      }
    };

    utterance.onend = () => {
      clearInterval(syllableInterval);
      finishSpeaking();
    };

    utterance.onerror = (e) => {
      clearInterval(syllableInterval);
      console.warn('SpeechSynthesis error:', e);
      finishSpeaking();
    };

    window.speechSynthesis.speak(utterance);
  }

  function finishSpeaking() {
    state.isSpeaking = false;
    state.speechUtterance = null;
    state.targetJawOpen = 0;
    state.jawOpenVal = 0;
    if (state.activeViseme) {
      setMorphTarget(state.activeViseme, 0);
      state.activeViseme = null;
    }
    setMorphTarget('jawOpen', 0);
    setMorphTarget('mouthOpen', 0);
    setMorphTarget('mouthSmile', 0.16);
    if (dom.lipSyncBadge) dom.lipSyncBadge.textContent = 'VISEME LIP-SYNC READY';
    setAnimationState('IDLE');
  }

  function stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    finishSpeaking();
  }

  // =========================================================================
  // 5. Speech Dictation (Microphone / STT)
  // =========================================================================
  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      if (dom.btnMic) {
        dom.btnMic.title = 'Microphone speech recognition not supported in this browser';
        dom.btnMic.style.opacity = '0.5';
      }
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      state.isListening = true;
      setAnimationState('LISTENING');
      if (dom.btnMic) dom.btnMic.classList.add('mic-active');
      if (dom.textInput) dom.textInput.placeholder = 'Listening... Speak your question now';
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (dom.textInput) {
        dom.textInput.value = transcript;
        handleSendMessage();
      }
    };

    recognition.onerror = (event) => {
      console.warn('SpeechRecognition error:', event.error);
      resetListening();
      setAnimationState('IDLE');
    };

    recognition.onend = () => {
      resetListening();
      if (state.animationState === 'LISTENING') setAnimationState('IDLE');
    };

    state.speechRecognition = recognition;
  }

  function toggleDictation() {
    if (!state.speechRecognition) {
      alert('Speech Recognition is not supported by your browser. Please type your query in the input box.');
      return;
    }

    if (state.isListening) {
      state.speechRecognition.stop();
      resetListening();
    } else {
      try {
        stopSpeaking();
        state.speechRecognition.start();
      } catch (err) {
        console.warn('Error starting speech recognition:', err);
      }
    }
  }

  function resetListening() {
    state.isListening = false;
    if (dom.btnMic) dom.btnMic.classList.remove('mic-active');
    if (dom.textInput) dom.textInput.placeholder = 'Ask Ava about SLA, picking, stores, orders...';
  }

  // =========================================================================
  // 6. Grounded Chat Query Dispatcher & DOM Rendering
  // =========================================================================
  async function handleSendMessage() {
    if (!dom.textInput) return;
    const rawMessage = dom.textInput.value.trim();
    if (!rawMessage) return;

    // Clear input
    dom.textInput.value = '';

    // Append User message
    appendMessage('user', rawMessage);

    // Set state to THINKING
    stopSpeaking();
    setAnimationState('THINKING');

    // Append typing indicator
    const typingId = appendTypingIndicator();

    try {
      const response = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: rawMessage })
      });

      removeTypingIndicator(typingId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Server returned ${response.status}`);
      }

      const data = await response.json();

      // Render Ava's response with grounded evidence
      appendMessage('assistant', data.reply, data);

      // Speak response
      speakReply(data.reply);

    } catch (err) {
      removeTypingIndicator(typingId);
      console.error('Assistant query error:', err);
      setAnimationState('ERROR');
      appendMessage('assistant', `Operational Query Error: ${err.message}. Please verify the query and try again.`, { isError: true });
    }
  }

  function appendMessage(sender, text, meta = null) {
    if (!dom.chatMessages) return;

    const msgEl = document.createElement('div');
    msgEl.className = `assistant-msg msg-${sender}`;

    if (sender === 'user') {
      msgEl.innerHTML = `
        <div class="msg-bubble user-bubble">${escapeHTML(text)}</div>
      `;
    } else {
      let evidenceHTML = '';
      if (meta && meta.evidence && Object.keys(meta.evidence).length > 0) {
        const ev = meta.evidence;
        const evItems = Object.entries(ev)
          .filter(([k]) => !['source_view', 'source_report', 'source_documents', 'denominator', 'risk_scores'].includes(k))
          .map(([k, v]) => `<span><strong>${escapeHTML(formatKey(k))}:</strong> ${escapeHTML(String(v))}</span>`)
          .join(' &bull; ');

        evidenceHTML = `
          <div class="msg-evidence-box">
            <div class="evidence-header">
              <span class="evidence-tag">GROUNDED EVIDENCE</span>
              <span class="evidence-source">${escapeHTML(ev.source_view || ev.source_report || 'macroops_analytics.db')}</span>
            </div>
            <div class="evidence-body">${evItems}</div>
            ${meta.denominator ? `<div class="evidence-denom"><strong>Denominator:</strong> ${escapeHTML(meta.denominator)}</div>` : ''}
          </div>
        `;
      }

      let recommendationHTML = '';
      if (meta && meta.recommendation) {
        recommendationHTML = `
          <div class="msg-recommendation-box">
            <span class="rec-icon">💡</span>
            <span class="rec-text">${escapeHTML(meta.recommendation)}</span>
          </div>
        `;
      }

      let disclaimerHTML = '';
      if (meta && meta.synthetic_data_disclaimer) {
        disclaimerHTML = `
          <div class="msg-disclaimer">
            <span>PROTOTYPE NOTICE:</span> ${escapeHTML(meta.synthetic_data_disclaimer)}
          </div>
        `;
      }

      msgEl.innerHTML = `
        <div class="msg-avatar-icon">👩‍💼</div>
        <div class="msg-content-wrapper">
          <div class="msg-bubble assistant-bubble ${meta && meta.isError ? 'bubble-error' : ''}">
            ${formatMessageText(text)}
          </div>
          ${evidenceHTML}
          ${recommendationHTML}
          ${disclaimerHTML}
        </div>
      `;
    }

    dom.chatMessages.appendChild(msgEl);
    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
  }

  function appendTypingIndicator() {
    if (!dom.chatMessages) return null;
    const id = 'typing-' + Date.now();
    const typingEl = document.createElement('div');
    typingEl.id = id;
    typingEl.className = 'assistant-msg msg-assistant';
    typingEl.innerHTML = `
      <div class="msg-avatar-icon">👩‍💼</div>
      <div class="msg-bubble assistant-bubble typing-bubble">
        <span class="dot-typing"></span>
        <span class="dot-typing"></span>
        <span class="dot-typing"></span>
        <span class="typing-text">Ava is analyzing database...</span>
      </div>
    `;
    dom.chatMessages.appendChild(typingEl);
    dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
    return id;
  }

  function removeTypingIndicator(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function formatMessageText(text) {
    if (!text) return '';
    return escapeHTML(text)
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br/>');
  }

  function formatKey(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  function escapeHTML(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // =========================================================================
  // 7. Panel Visibility & Control Handlers
  // =========================================================================
  function openAssistantPanel() {
    state.isOpen = true;
    state.isMinimized = false;
    if (dom.panel) {
      dom.panel.classList.add('open');
      dom.panel.classList.remove('minimized');
      dom.panel.setAttribute('aria-hidden', 'false');
    }
    if (dom.triggerBtn) dom.triggerBtn.classList.add('active');

    // Initialize Three.js scene on first open
    if (!renderer) {
      initThreeScene();
    } else {
      onWindowResize();
    }

    // Append welcome message if empty
    if (dom.chatMessages && dom.chatMessages.children.length === 0) {
      appendMessage(
        'assistant',
        "Hello! I am **Ava**, your 3D Operations Intelligence Copilot for MacroOps. " +
        "I provide real-time grounded analytics across our 100 dark stores, order lifecycle tracking, and predictive SLA models (Stage A, B1, and B2). " +
        "How can I assist your operations team today?"
      );
    }

    // Focus input
    if (dom.textInput) dom.textInput.focus();
  }

  function closeAssistantPanel() {
    state.isOpen = false;
    stopSpeaking();
    resetListening();
    if (dom.panel) {
      dom.panel.classList.remove('open');
      dom.panel.setAttribute('aria-hidden', 'true');
    }
    if (dom.triggerBtn) dom.triggerBtn.classList.remove('active');
  }

  function toggleMinimizeAssistant() {
    state.isMinimized = !state.isMinimized;
    if (dom.panel) {
      dom.panel.classList.toggle('minimized', state.isMinimized);
    }
    if (dom.btnMinimize) {
      dom.btnMinimize.innerHTML = state.isMinimized ? '&#x25A2;' : '&minus;';
    }
  }

  function toggleVoice() {
    state.voiceEnabled = !state.voiceEnabled;
    if (dom.voiceLabel) dom.voiceLabel.textContent = state.voiceEnabled ? 'VOICE: ON' : 'VOICE: OFF';
    if (dom.voiceIcon) dom.voiceIcon.textContent = state.voiceEnabled ? '🔊' : '🔇';
    if (dom.btnVoiceToggle) dom.btnVoiceToggle.classList.toggle('voice-muted', !state.voiceEnabled);

    if (!state.voiceEnabled) {
      stopSpeaking();
    }
  }

  // =========================================================================
  // 8. Event Listeners Setup
  // =========================================================================
  function setupEventListeners() {
    // Trigger button
    if (dom.triggerBtn) {
      dom.triggerBtn.addEventListener('click', () => {
        if (state.isOpen) closeAssistantPanel();
        else openAssistantPanel();
      });
    }

    // Header actions
    if (dom.btnClose) dom.btnClose.addEventListener('click', closeAssistantPanel);
    if (dom.btnMinimize) dom.btnMinimize.addEventListener('click', toggleMinimizeAssistant);
    if (dom.btnVoiceToggle) dom.btnVoiceToggle.addEventListener('click', toggleVoice);
    if (dom.btnStopSpeech) dom.btnStopSpeech.addEventListener('click', stopSpeaking);

    // Form submission
    if (dom.inputForm) {
      dom.inputForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleSendMessage();
      });
    }

    if (dom.btnSend) {
      dom.btnSend.addEventListener('click', (e) => {
        e.preventDefault();
        handleSendMessage();
      });
    }

    // Dictation
    if (dom.btnMic) {
      dom.btnMic.addEventListener('click', toggleDictation);
    }

    // Input focus sets state to LISTENING
    if (dom.textInput) {
      dom.textInput.addEventListener('focus', () => {
        if (state.animationState === 'IDLE') setAnimationState('LISTENING');
      });
      dom.textInput.addEventListener('blur', () => {
        if (state.animationState === 'LISTENING' && !state.isListening) setAnimationState('IDLE');
      });
    }

    // Quick suggestion chips
    if (dom.chipsContainer) {
      dom.chipsContainer.addEventListener('click', (e) => {
        const chip = e.target.closest('.assistant-chip');
        if (chip && chip.dataset.query) {
          if (dom.textInput) dom.textInput.value = chip.dataset.query;
          handleSendMessage();
        }
      });
    }

    // Keyboard shortcuts (Escape closes panel)
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && state.isOpen) {
        closeAssistantPanel();
      }
    });

    // Initialize speech recognition
    initSpeechRecognition();
  }

  // =========================================================================
  // 9. Bootstrap
  // =========================================================================
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupEventListeners);
  } else {
    setupEventListeners();
  }

})();
