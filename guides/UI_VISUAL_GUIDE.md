# Screen Recorder - Visual Guide & UI Layout

## 🎨 Application Interface Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  Screen Recorder - Professional Screen Sharing          [_] [□] [X]│
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│         📹 Screen Recorder & Sharing                             │
│         ─────────────────────────────────────────                │
│                                                                    │
│  Settings Row:                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Resolution: [1920x1080 ▼]  FPS: [30] ⬆⬇  [☑ 🔒 Blur]    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Status Display:                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Status: 🔴 RECORDING                                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Live Preview (When recording):                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                             │  │
│  │              [Live preview shows here]                     │  │
│  │         [480x270px - updates every 100ms]                │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Timer Display:                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      00:01:23                              │  │
│  │                   (32pt Red Text)                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Frame Counter:                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Frames: 2541                                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Control Buttons:                                                 │
│  ┌─────────────────────────┐     ┌──────────────────────────┐    │
│  │  ▶ START SHARING        │     │  ⏹ STOP SHARING         │    │
│  │  (Green Gradient)       │     │  (Red Gradient)          │    │
│  │  200x60px               │     │  200x60px - Disabled     │    │
│  └─────────────────────────┘     └──────────────────────────┘    │
│                                                                    │
│  Info:                                                            │
│  📁 Recordings saved to: d:\Desktop\screenshare\recordings\      │
│                                                                    │
├──────────────────────────────────────────────────────────────────┤
│ Status: Recording in progress...                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Control Elements

### Resolution Selector
```
┌─────────────────────────┐
│ Resolution: [▼]         │
│  • 1920x1080 (selected) │
│  • 1280x720             │
│  • 1024x768             │
│  • 800x600              │
└─────────────────────────┘
```

### FPS Spinbox
```
┌──────────────┐
│ FPS: [30]  ⬆ │
│      [30]  ⬇ │
└──────────────┘
Range: 10-60 FPS
```

### Face Blur Checkbox
```
┌──────────────────────┐
│ ☑ 🔒 Blur Faces    │
│ (enabled/disabled)   │
└──────────────────────┘
```

### Start Button
```
┌─────────────────────────────┐
│   ▶ START SHARING           │
│                              │
│  Green Gradient              │
│  200x60px                    │
│  Bold 13pt Font              │
│                              │
│  States:                     │
│  • Enabled: Bright Green     │
│  • Hover: Darker Green       │
│  • Pressed: Even Darker      │
│  • Disabled: Gray            │
└─────────────────────────────┘
```

### Stop Button
```
┌─────────────────────────────┐
│   ⏹ STOP SHARING            │
│                              │
│  Red Gradient                │
│  200x60px                    │
│  Bold 13pt Font              │
│                              │
│  States:                     │
│  • Enabled: Bright Red       │
│  • Hover: Darker Red         │
│  • Pressed: Even Darker      │
│  • Disabled: Gray            │
└─────────────────────────────┘
```

---

## 🎬 UI States

### Ready State (Before Recording)
```
┌───────────────────────────────────┐
│ Status: ✅ Ready                  │
│ Preview: "Live Preview (When...)" │
│ Timer: 00:00:00                   │
│ Frames: 0                         │
│ START: ✅ Enabled (Green)         │
│ STOP: ❌ Disabled (Gray)          │
│ Settings: ✅ Enabled              │
└───────────────────────────────────┘
```

### Recording State (During Recording)
```
┌───────────────────────────────────┐
│ Status: 🔴 RECORDING              │
│ Preview: [Live video feed]        │
│ Timer: 00:01:45 (counting up)     │
│ Frames: 2745 (updating)           │
│ START: ❌ Disabled (Gray)         │
│ STOP: ✅ Enabled (Red)            │
│ Settings: ❌ Disabled (Locked)    │
└───────────────────────────────────┘
```

### Stopped State (After Recording)
```
┌───────────────────────────────────┐
│ Status: ⏹ STOPPED                 │
│ Preview: "Live Preview (When...)" │
│ Timer: 00:01:45 (frozen)          │
│ Frames: 2745 (final count)        │
│ START: ✅ Enabled (Green)         │
│ STOP: ❌ Disabled (Gray)          │
│ Settings: ✅ Enabled              │
└───────────────────────────────────┘
```

### Error State
```
┌───────────────────────────────────┐
│ Status: ❌ ERROR - [Error Msg]    │
│ Preview: "Live Preview (When...)" │
│ Timer: 00:00:XX (stopped)         │
│ Frames: XXXX (final)              │
│ START: ✅ Enabled (Green)         │
│ STOP: ❌ Disabled (Gray)          │
│ Settings: ✅ Enabled              │
└───────────────────────────────────┘
```

---

## 🎨 Color Palette

### Theme Colors
```
Primary Dark:     #0d0d0d  ■■■■■  (Background)
Primary Text:     #FFFFFF  ■■■■■  (Text)
Primary Accent:   #667eea  ■■■■■  (Purple)
Secondary Accent: #764ba2  ■■■■■  (Darker Purple)
Success/Start:    #4CAF50  ■■■■■  (Green)
Warning/Stop:     #FF6B6B  ■■■■■  (Red)
Info/Timer:       #87CEEB  ■■■■■  (Sky Blue)
```

### Gradient Buttons
```
Start (Green):
┌─────────────────────┐
│  #4CAF50  ▶  #45a049│
│  ──────────────────│
│  (Left to Right)    │
└─────────────────────┘

Stop (Red):
┌─────────────────────┐
│  #FF6B6B  ▶  #ff5555│
│  ──────────────────│
│  (Left to Right)    │
└─────────────────────┘

Accent (Purple):
┌─────────────────────┐
│  #667eea  ▶  #764ba2│
│  ──────────────────│
│  (Diagonal 135°)    │
└─────────────────────┘
```

---

## 📐 Layout Dimensions

### Window Size
```
Default:        1000x700 pixels
Minimum:        800x600 pixels (approximate)
Resizable:      Yes
Aspect Ratio:   Any
```

### Component Sizes
```
Title Label:        Full width, 50px height
Settings Row:       Full width, 50px height
Status Display:     Full width, 50px height
Preview:            Full width, 300px height
Timer Display:      Full width, 80px height
Frame Counter:      Full width, 35px height
Button Row:         Full width, 80px height
Info Text:          Full width, 30px height
Margins:            20px all around
Spacing:            15-20px between rows
```

### Button Dimensions
```
Start/Stop Buttons:
  Width:            200px
  Height:           60px
  Padding:          15px
  Border Radius:    8px
  Font Size:        13pt Bold
  Hover Area:       +5px outer
```

---

## 📊 Timer Display

### Format
```
HH:MM:SS
││└─── Seconds (00-59)
│└──── Minutes (00-59)
└───── Hours (00-23+)

Examples:
  00:00:00  ← Starting
  00:01:23  ← 1 minute 23 seconds
  01:05:47  ← 1 hour 5 minutes 47 seconds
  10:30:00  ← 10 hours 30 minutes
```

### Display Style
```
Font:         Courier New (monospace)
Size:         32pt
Weight:       Bold
Color:        #FF6B6B (Bright Red)
Background:   #000000 (Black)
Padding:      20px
Border:       2px solid #FF6B6B
Border-Radius: 10px
Text-Align:   Center
```

---

## 📸 Live Preview

### Preview Window
```
┌──────────────────────────────────┐
│  Live Preview (When recording)   │ ← Placeholder text
│                                   │
│    [Live Screen Capture Here]    │ ← Shows when recording
│    [With Face Blur Applied]      │
│    [480x270 resolution]          │
│                                   │
│    [Updates every 100ms]         │
│                                   │
└──────────────────────────────────┘

Dimensions:   480x270 pixels
Update Rate:  100ms (10 FPS preview)
Aspect Ratio: 16:9
```

### Preview States
```
Not Recording:
  Display: "Live Preview (When recording)"
  Color: Gray (#666666)
  Background: Black (#000000)

Recording:
  Display: Live video stream
  Showing: Screen capture
  Effects: Face blur (if enabled)
  
Recording with Face Blur OFF:
  Display: Raw screen
  
Recording with Face Blur ON:
  Display: Screen + blurred faces
```

---

## 🎮 Interaction Flow

### Recording Flow
```
START
  │
  ├─→ Check Settings
  │   ├─ Resolution
  │   └─ FPS
  │
  ├─→ Initialize Recording
  │   ├─ Create video file
  │   └─ Load face cascade (if blur enabled)
  │
  ├─→ Enter Recording Loop
  │   ├─ Capture screen frame
  │   ├─ Apply blur (if enabled)
  │   ├─ Encode frame
  │   ├─ Write to file
  │   └─ Update display every 100ms
  │
  └─→ Stop
      ├─ Finalize video file
      ├─ Update status
      └─ Show completion message
```

### User Interaction
```
1. User adjusts settings (optional)
   ├─ Select Resolution
   ├─ Set FPS
   └─ Enable/Disable Face Blur

2. User clicks START
   ├─ Button changes to disabled
   ├─ Settings lock
   ├─ Timer starts
   └─ Preview updates

3. User watches recording
   ├─ Monitor timer
   ├─ View live preview
   └─ See frame count

4. User clicks STOP
   ├─ Recording ends
   ├─ Settings unlock
   ├─ Video saves
   └─ Status updates

5. User can START again
```

---

## ⌨️ Keyboard Shortcuts

### Available Shortcuts
```
Shortcut    │ Action
────────────┼────────────────────────
Alt+F4      │ Close Application
            │ (Stops recording if active)
────────────┼────────────────────────
Tab         │ Focus next control
────────────┼────────────────────────
Shift+Tab   │ Focus previous control
────────────┼────────────────────────
Space       │ Toggle checkbox (if focused)
────────────┼────────────────────────
Enter/Return│ Activate button (if focused)
────────────┼────────────────────────
↑/↓         │ Adjust spinbox (if focused)
```

---

## 📱 Responsive Design

### Minimum Window Size
```
Width:  800px
Height: 600px

At minimum size:
  ✓ All buttons visible
  ✓ All controls accessible
  ✓ Text readable
  ✓ Preview resized proportionally
```

### Maximum Expansion
```
Width:  2560px (4K)
Height: 1440px

At maximum size:
  ✓ Elements scale proportionally
  ✓ Padding adjusts
  ✓ Preview expands
  ✓ All controls remain accessible
```

### Aspect Ratio Flexibility
```
Window can be:
  • Wider (landscape): 16:9, 16:10, 21:9
  • Taller (portrait): 9:16, 10:16
  • Square: 1:1

UI adapts automatically
```

---

## 🔒 Face Blur Visual

### Detection & Blur Process
```
Original Frame:
┌────────────────────────┐
│  Person's Face         │
│  [Clearly Visible]     │
│                        │
│  Details:              │
│  • Eyes visible        │
│  • Nose visible        │
│  • Mouth visible       │
└────────────────────────┘

With Face Blur Enabled:
┌────────────────────────┐
│  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  │
│  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  │
│  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  │
│                        │
│  All facial details    │
│  completely obscured   │
└────────────────────────┘
```

### Blur Settings Visualization
```
Light Blur (BLUR_SIGMA=15, BLUR_KSIZE=31x31):
▒░░░░░░░░░░░░░░░░░░░░░░░░░░░  ← Some details visible

Medium Blur (BLUR_SIGMA=30, BLUR_KSIZE=51x51):
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ← All details hidden

Strong Blur (BLUR_SIGMA=50, BLUR_KSIZE=71x71):
██████████████████████████████  ← Maximum privacy
```

---

## 📊 Status Indicators

### Status Messages
```
Status          │ Icon │ Color   │ Meaning
────────────────┼──────┼─────────┼─────────────────
Ready           │ ✅   │ Green   │ Can start recording
🔴 RECORDING    │ ●    │ Red     │ Recording in progress
⏹ STOPPED       │ ⏹    │ Orange  │ Recording complete
❌ ERROR        │ ❌   │ Red     │ Error occurred
```

### Status Bar Messages
```
State              │ Status Bar Message
─────────────────────────────────────────────
Before Recording   │ Ready to record
Starting Record    │ Recording in progress...
During Recording   │ Recording: 2541 frames
Face Blur Enabled  │ Face blur enabled
Face Blur Toggle   │ Face blur disabled/enabled
Stopping Record    │ Recording stopped. Saved 2541 frames.
Error State        │ Recording error: [error details]
```

---

## 🖱️ Mouse Interactions

### Hover Effects
```
Element         │ Normal State    │ Hover State
────────────────┼─────────────────┼──────────────────
START Button    │ Bright Green    │ Darker Green
STOP Button     │ Bright Red      │ Darker Red
Resolution Box  │ Purple Border   │ Dark Purple Border
FPS Spinbox     │ Purple Border   │ Dark Purple Border
Blur Checkbox   │ Purple Border   │ Dark Purple Border
Spinbox Buttons │ Purple         │ Dark Purple
```

### Click Effects
```
Button          │ Click Effect
────────────────┼──────────────────────────────
START           │ Darkest Green + Recording
STOP            │ Darkest Red + Stop Recording
Resolution      │ Dropdown menu appears
FPS Up/Down     │ Value increments/decrements
Checkbox        │ Toggle on/off
```

### Cursor Changes
```
Element     │ Cursor Type
────────────┼─────────────────
Button      │ Pointing Hand
Text Box    │ I-beam (text)
Checkbox    │ Pointing Hand
Label       │ Normal Arrow
```

---

## 🎞️ Animation Effects

### Smooth Transitions
```
Button Hover:  100ms fade
Status Update: Instant change
Timer Update:  Real-time (every 100ms)
Preview:       Real-time (every 100ms)
Frame Counter: Real-time (every frame)
```

### Visual Feedback
```
Action              │ Feedback
─────────────────────┼──────────────────────────
Click START         │ Button depresses + status changes
Click STOP          │ Button depresses + preview hides
Checkbox Toggle     │ Checkbox checks/unchecks
Settings Change     │ Status bar updates
Recording Progress  │ Timer increments smoothly
```

---

## 📋 Complete Layout Tree

```
MainWindow (1000x700)
├── CentralWidget
│   └── MainLayout (Vertical)
│       ├── Title Label
│       │   Font: 24pt Bold
│       │   Background: Purple Gradient
│       │
│       ├── Settings Layout (Horizontal)
│       │   ├── Resolution Label + ComboBox
│       │   ├── FPS Label + SpinBox
│       │   ├── Blur CheckBox
│       │   └── Stretch
│       │
│       ├── Status Display Layout (Vertical)
│       │   ├── Status Label (✅ Ready)
│       │   ├── Preview Label (Live preview)
│       │   ├── Timer Layout (HH:MM:SS)
│       │   └── Frame Counter Label
│       │
│       ├── Control Buttons Layout (Horizontal)
│       │   ├── Stretch
│       │   ├── START Button (Green)
│       │   ├── STOP Button (Red)
│       │   └── Stretch
│       │
│       ├── Progress Bar (Hidden)
│       │
│       └── Info Label
│           Recordings directory path
│
└── StatusBar
    Recording status message
```

---

**Visual Design Complete! 🎨**

All UI elements are precisely designed for professional use with optimal visibility and user experience.
