# Object Tags - Detailed Reference

Object tags display data elements in the labeling interface. Each object tag requires a `name` parameter and typically a `value` parameter to reference task data.

## Audio

Display audio with waveform visualization.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field containing URL/path to audio
- `defaultspeed` (default="1"): Playback speed (0.5-2)
- `defaultscale` (default="1"): Waveform y-scale
- `defaultzoom` (default="1"): Zoom level (1-1500)
- `defaultvolume` (default="1"): Volume (0-1)
- `hotkey`: Play/pause hotkey
- `sync`: Object name to sync with (for video/paragraphs)
- `height` (default="96"): Total height of player
- `waveheight` (default="32"): Min height for split channels
- `spectrogram` (default="false"): Show spectrogram on load
- `splitchannels` (default="false"): Display channels separately
- `decoder` (default="webaudio"): Decoder type ("webaudio", "ffmpeg", "none")
- `player` (default="html5"): Player type ("html5", "webaudio")

**Example - Basic audio:**
```xml
<Audio name="audio" value="$audio" />
```

**Example - Audio classification:**
```xml
<Audio name="audio" value="$audio" />
<Choices name="ch" toName="audio">
  <Choice value="Positive" />
  <Choice value="Negative" />
</Choices>
```

**Example - Audio transcription:**
```xml
<Audio name="audio" value="$audio" />
<TextArea name="ta" toName="audio" />
```

**Example - Multi-channel:**
```xml
<Audio name="audio" value="$audio" splitchannels="true" />
```

---

## Chat

Display conversational transcripts with optional LLM integration. (Enterprise/Starter Cloud only)

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field with chat message array (or empty array)
- `messageroles`: Comma-separated list of roles user can create (default: "user" if llm set, "user,assistant" otherwise)
- `editable`: Whether messages are editable (true/false or comma-separated roles)
- `minmessages`: Minimum total messages required to submit
- `maxmessages`: Maximum total messages allowed
- `llm`: Model for auto-replies, format: `<provider>/<model>` (e.g., "openai/gpt-4.1-nano")

**Input data format:**
```json
{
  "chat": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

**Supported roles:** user, assistant, system, tool, developer

**Example - Basic chat:**
```xml
<Chat name="chat" value="$chat" toName="chat" />
```

**Example - Chat with LLM and evaluation:**
```xml
<Chat name="chat" value="$chat" llm="openai/gpt-4.1-nano" />
<View visibleWhen="region-selected" whenRole="assistant">
  <Rating name="quality" toName="chat" perRegion="true" />
</View>
```

**Example - Role-based controls:**
```xml
<View visibleWhen="region-selected" whenRole="user">
  <Choices name="choices" toName="chat" perRegion="true">
    <Choice value="User choice 1" />
    <Choice value="User choice 2" />
  </Choices>
</View>
```

---

## HyperText

Display HTML content.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field containing HTML
- `inline` (default="false"): Display inline with other elements
- `html` (default="false"): Render as HTML (vs plain text)

---

## Image

Display images for annotation.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field containing URL/path to image
- `brightness`: Brightness adjustment (0-2)
- `contrast`: Contrast adjustment (0-2)
- `rotate`: Rotation in degrees
- `zoom`: Zoom level

---

## List

Display a list of items.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field with list
- `title`: List title
- `allowEmptyChoice`: Allow empty selection

---

## Paragraphs

Display paragraph text with optional dialogue layout.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field with paragraphs
- `layout`: "dialogue" or other layout options
- `audioUrl`: Audio file to sync with
- `sync`: Object name to sync with
- `showplayer` (default="false"): Show audio player

**Example - Dialogue with audio sync:**
```xml
<Paragraphs audioUrl="$audio" sync="audio-1" name="txt-1" value="$text" layout="dialogue" />
```

---

## PDF

Display PDF documents for annotation. Supports up to 100 pages.

**Parameters:**
- `value` (required): Data field containing URL to PDF

**Features:**
- Zoom, rotation support
- OCR validation (Enterprise with `<OcrLabels>`)

**Example - PDF classification:**
```xml
<Pdf name="pdf" value="$pdf" />
<Choices name="choices" toName="pdf">
  <Choice value="Legal" />
  <Choice value="Financial" />
  <Choice value="Technical" />
</Choices>
```

**Example - PDF OCR (Enterprise):**
```xml
<OcrLabels name="ocr" toName="pdf">
  <Label value="Typo" />
  <Label value="Incorrect amount" />
</OcrLabels>
<Pdf name="pdf" value="$pdf" />
```

**PDF styling:**
```xml
<Style>
  .htx-pdf { height: calc(100vh - 250px); }
</Style>
```

---

## Table

Display tabular data.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field with table data

---

## Text

Display text content for annotation.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field containing text
- `inline` (default="false"): Display inline
- `maxSubmissions`: Max text submissions

**Example - Simple text:**
```xml
<Text name="text" value="$text" />
```

**Example - Text with NER:**
```xml
<Labels name="ner" toName="text">
  <Label value="PER" />
  <Label value="ORG" />
</Labels>
<Text name="text" value="$text" />
```

---

## TimeSeries

Display time series data.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field with time series data

---

## Video

Display video content.

**Parameters:**
- `name` (required): Element name
- `value` (required): Data field containing URL/path to video
- `sync`: Object name to sync with (e.g., audio)

**Example - Video with audio sync:**
```xml
<Video name="video" value="$video" sync="audio-1" />
<Audio name="audio" value="$audio" sync="video-1" />
```
