# Complete Template Examples

Organized by task type for quick reference.

## Computer Vision

### Object Detection (Bounding Boxes)
```xml
<View>
  <Header value="Select objects in the image" />
  <RectangleLabels name="labels" toName="image">
    <Label value="Person" background="#ff0000" />
    <Label value="Car" background="#00ff00" />
    <Label value="Dog" background="#0000ff" />
  </RectangleLabels>
  <Image name="image" value="$image" />
</View>
```

### Semantic Segmentation (Polygons)
```xml
<View>
  <Header value="Segment the image" />
  <PolygonLabels name="labels" toName="image">
    <Label value="Road" />
    <Label value="Sidewalk" />
    <Label value="Building" />
  </PolygonLabels>
  <Image name="image" value="$image" />
</View>
```

### Key Point Annotation
```xml
<View>
  <Header value="Mark keypoints" />
  <KeyPointLabels name="labels" toName="image">
    <Label value="Left Eye" />
    <Label value="Right Eye" />
    <Label value="Nose" />
    <Label value="Mouth" />
  </KeyPointLabels>
  <Image name="image" value="$image" />
</View>
```

### Image Classification
```xml
<View>
  <Header value="What's in this image?" />
  <Choices name="category" toName="image" choice="single" showInline="true">
    <Choice value="Landscape" />
    <Choice value="Portrait" />
    <Choice value="Animal" />
    <Choice value="Object" />
  </Choices>
  <Image name="image" value="$image" />
</View>
```

### Image Captioning
```xml
<View>
  <Header value="Describe this image" />
  <TextArea name="caption" toName="image" />
  <Image name="image" value="$image" />
</View>
```

### Multi-Image Classification
```xml
<View>
  <Header value="Are these images similar?" />
  <Image name="image1" value="$image1" />
  <Image name="image2" value="$image2" />
  <Choices name="similar" toName="image1">
    <Choice value="Yes" />
    <Choice value="No" />
  </Choices>
</View>
```

---

## Natural Language Processing

### Text Classification (Single Label)
```xml
<View>
  <Header value="Classify the text" />
  <Choices name="sentiment" toName="text" choice="single-radio">
    <Choice value="Positive" />
    <Choice value="Negative" />
    <Choice value="Neutral" />
  </Choices>
  <Text name="text" value="$text" />
</View>
```

### Text Classification (Multi-Label)
```xml
<View>
  <Header value="Select all that apply" />
  <Choices name="topics" toName="text" choice="multiple">
    <Choice value="Politics" />
    <Choice value="Sports" />
    <Choice value="Entertainment" />
    <Choice value="Technology" />
  </Choices>
  <Text name="text" value="$text" />
</View>
```

### Named Entity Recognition (NER)
```xml
<View>
  <Header value="Highlight named entities" />
  <Labels name="ner" toName="text">
    <Label value="PER" background="#e74c3c" />
    <Label value="ORG" background="#3498db" />
    <Label value="LOC" background="#2ecc71" />
    <Label value="DATE" background="#f39c12" />
  </Labels>
  <Text name="text" value="$text" />
</View>
```

### Relation Extraction
```xml
<View>
  <Header value="Identify relations between entities" />
  <Relations>
    <Relation value="works_for" />
    <Relation value="lives_in" />
    <Relation value="is_friends_with" />
  </Relations>
  <Labels name="entities" toName="text">
    <Label value="Person" />
    <Label value="Organization" />
    <Label value="Location" />
  </Labels>
  <Text name="text" value="$text" />
</View>
```

### Text Summarization
```xml
<View>
  <Header value="Summarize the text" />
  <TextArea name="summary" toName="text" rows="5" />
  <Text name="text" value="$text" />
</View>
```

### Taxonomy Classification
```xml
<View>
  <Header value="Select the category" />
  <Taxonomy name="category" toName="text">
    <Choice value="Technology">
      <Choice value="Software" />
      <Choice value="Hardware" />
    </Choice>
    <Choice value="Science">
      <Choice value="Physics" />
      <Choice value="Biology" />
      <Choice value="Chemistry" />
    </Choice>
    <Choice value="Arts">
      <Choice value="Music" />
      <Choice value="Painting" />
    </Choice>
  </Taxonomy>
  <Text name="text" value="$text" />
</View>
```

---

## Audio Processing

### Audio Classification
```xml
<View>
  <Header value="Classify the audio" />
  <Audio name="audio" value="$audio" />
  <Choices name="category" toName="audio" choice="single">
    <Choice value="Music" />
    <Choice value="Speech" />
    <Choice value="Noise" />
  </Choices>
</View>
```

### Audio Transcription
```xml
<View>
  <Header value="Transcribe the audio" />
  <Audio name="audio" value="$audio" />
  <TextArea name="transcription" toName="audio" />
</View>
```

### Audio Segmentation (Region Labeling)
```xml
<View>
  <Header value="Label audio segments" />
  <Labels name="sounds" toName="audio">
    <Label value="Speech" />
    <Label value="Music" />
    <Label value="Silence" />
  </Labels>
  <Audio name="audio" value="$audio" />
</View>
```

### Audio Classification with Segments
```xml
<View>
  <Header value="Classify each segment" />
  <Labels name="segment_labels" toName="audio">
    <Label value="Speaker A" />
    <Label value="Speaker B" />
  </Labels>
  <Audio name="audio" value="$audio" />
</View>
```

---

## Chat & Conversational AI

### Basic Chat Evaluation
```xml
<View>
  <Header value="Evaluate the conversation" />
  <Chat name="chat" value="$chat" />
  <Choices name="quality" toName="chat">
    <Choice value="Excellent" />
    <Choice value="Good" />
    <Choice value="Fair" />
    <Choice value="Poor" />
  </Choices>
</View>
```

### Chat with LLM Auto-Replies
```xml
<View>
  <Header value="Continue the conversation" />
  <Chat name="chat" value="$chat" llm="openai/gpt-4.1-nano" />
</View>
```

### Message-Level Evaluation
```xml
<View>
  <Style>
    .htx-chat { flex-grow: 1; }
    .htx-chat-sidepanel { flex: 300px 0 0; border-left: 2px solid #ccc; padding-left: 16px; }
  </Style>
  <View style="display: flex; width: 100%; gap: 1em;">
    <Chat name="chat" value="$chat" editable="true" />
    <View className="htx-chat-sidepanel">
      <Header value="Rate each message" />
      <View visibleWhen="region-selected" whenRole="assistant">
        <Header value="Assistant message" />
        <Rating name="quality" toName="chat" perRegion="true" />
      </View>
      <View visibleWhen="region-selected" whenRole="user">
        <Header value="User message" />
        <Choices name="user_intent" toName="chat" perRegion="true">
          <Choice value="Question" />
          <Choice value="Request" />
          <Choice value="Feedback" />
        </Choices>
      </View>
    </View>
  </View>
</View>
```

### Multi-Turn Chat Evaluation
```xml
<View>
  <Header value="Evaluate conversation quality" />
  <Chat name="chat" value="$chat" />
  <Rating name="overall_quality" toName="chat" maxRating="5" />
  <TextArea name="feedback" toName="chat" placeholder="Any additional feedback?" />
</View>
```

---

## PDF & Document

### PDF Classification
```xml
<View>
  <Header value="Classify the document" />
  <Pdf name="pdf" value="$pdf" />
  <Choices name="doc_type" toName="pdf" choice="single">
    <Choice value="Legal" />
    <Choice value="Financial" />
    <Choice value="Technical" />
    <Choice value="Other" />
  </Choices>
</View>
```

### PDF OCR (Enterprise)
```xml
<View>
  <Header value="Validate OCR and fix errors" />
  <OcrLabels name="ocr" toName="pdf">
    <Label value="Typo" />
    <Label value="Wrong number" />
    <Label value="Missing text" />
  </OcrLabels>
  <Pdf name="pdf" value="$pdf" />
</View>
```

### Document Extraction
```xml
<View>
  <Header value="Extract information" />
  <Pdf name="pdf" value="$pdf" />
  <View style="display: flex; gap: 1rem;">
    <View style="flex: 1;">
      <Header value="Document Type" />
      <Choices name="doc_type" toName="pdf" choice="single">
        <Choice value="Invoice" />
        <Choice value="Receipt" />
        <Choice value="Contract" />
      </Choices>
    </View>
    <View style="flex: 1;">
      <Header value="Total Amount" />
      <TextArea name="amount" toName="pdf" placeholder="Enter amount" />
    </View>
  </View>
</View>
```

---

## Multi-Modal

### Image + Text Annotation
```xml
<View>
  <Header value="Annotate image and describe it" />
  <View style="display: flex; gap: 1rem;">
    <View style="flex: 1;">
      <Image name="image" value="$image" />
      <RectangleLabels name="objects" toName="image">
        <Label value="Object" />
      </RectangleLabels>
    </View>
    <View style="flex: 1;">
      <Header value="Description" />
      <TextArea name="description" toName="image" />
    </View>
  </View>
</View>
```

### Video with Audio
```xml
<View>
  <Header value="Annotate video" />
  <Video name="video" value="$video" sync="audio-1" />
  <Labels name="events" toName="video">
    <Label value="Action" />
    <Label value="Dialog" />
  </Labels>
  <Audio name="audio" value="$audio" sync="video-1" />
  <TextArea name="transcript" toName="audio" />
</View>
```

---

## Ranking & Scoring

### Visual Ranker
```xml
<View>
  <Header value="Rank by preference" />
  <Image name="image1" value="$image1" />
  <Image name="image2" value="$image2" />
  <Ranker name="preference" toName="image1">
    <Choice value="Prefer left" />
    <Choice value="Prefer right" />
  </Ranker>
</View>
```

### Pairwise Comparison
```xml
<View>
  <Header value="Which one is better?" />
  <View style="display: flex; gap: 1rem;">
    <View style="flex: 1;">
      <Text name="option1" value="$option1" />
    </View>
    <View style="flex: 1;">
      <Text name="option2" value="$option2" />
    </View>
  </View>
  <Pairwise name="comparison" toName="option1">
    <Choice value="First" />
    <Choice value="Second" />
  </Pairwise>
</View>
```

---

## Advanced Patterns

### Two-Stage Classification
```xml
<View>
  <Header value="Step 1: Choose category" />
  <Choices name="category" toName="text" choice="single">
    <Choice value="News" />
    <Choice value="Sports" />
    <Choice value="Weather" />
  </Choices>

  <View visibleWhen="choice-selected" whenTagName="category" whenChoiceValue="News">
    <Header value="Step 2: News subcategory" />
    <Choices name="subcategory" toName="text" choice="single">
      <Choice value="Politics" />
      <Choice value="Business" />
      <Choice value="Technology" />
    </Choices>
  </View>

  <View visibleWhen="choice-selected" whenTagName="category" whenChoiceValue="Sports">
    <Header value="Step 2: Sports subcategory" />
    <Choices name="subcategory" toName="text" choice="single">
      <Choice value="Football" />
      <Choice value="Basketball" />
      <Choice value="Tennis" />
    </Choices>
  </View>

  <Text name="text" value="$text" />
</View>
```

### Region-Specific Classification
```xml
<View>
  <Header value="Classify each named entity" />
  <Labels name="entities" toName="text">
    <Label value="Person" />
    <Label value="Organization" />
  </Labels>
  <Text name="text" value="$text" />
  <View visibleWhen="region-selected" whenLabelValue="Person">
    <Choices name="person_type" toName="text" perRegion="true">
      <Choice value="Athlete" />
      <Choice value="Politician" />
      <Choice value="Celebrity" />
      <Choice value="Other" />
    </Choices>
  </View>
  <View visibleWhen="region-selected" whenLabelValue="Organization">
    <Choices name="org_type" toName="text" perRegion="true">
      <Choice value="Company" />
      <Choice value="Government" />
      <Choice value="Non-profit" />
    </Choices>
  </View>
</View>
```

### Validated Annotations
```xml
<View>
  <Header value="Required annotations" />
  <Choices name="category" toName="text" choice="single" required="true" requiredMessage="Please select a category">
    <Choice value="A" />
    <Choice value="B" />
    <Choice value="C" />
  </Choices>
  <Labels name="entities" toName="text">
    <Label value="Entity" maxUsages="3" />
  </Labels>
  <Text name="text" value="$text" />
</View>
```
