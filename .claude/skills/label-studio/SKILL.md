---
name: label-studio
description: Label Studio template design reference for creating custom labeling configurations (XML-like configs). Use when creating, modifying, or troubleshooting Label Studio templates for data annotation tasks including image labeling (bounding boxes, polygons, keypoints), text annotation (NER, classification, relation extraction), audio transcription, chat evaluation, PDF/OCR annotation, video labeling, and multi-modal tasks.
---

# Label Studio Template Design Reference

## Quick Start

Label Studio uses XML-like tags to configure labeling interfaces. All configurations must be wrapped in a `<View>` tag.

```xml
<View>
  <ControlTags toName="objectName" />
  <ObjectTags name="objectName" value="$dataField" />
</View>
```

**Essential rules:**
- Every control tag requires a `toName` parameter that matches the `name` of an object tag
- All tags require a `name` parameter
- Variables use `$` prefix (e.g., `$value`) to reference task data fields

## Core Tag Categories

### 1. Object Tags (Display Data)
Tags that display data elements in the labeling interface.

| Tag | Purpose | Data Types |
|-----|---------|------------|
| `<Text>` | Display text content | text |
| `<Image>` | Display images | image |
| `<Audio>` | Play audio with waveform | audio |
| `<Video>` | Play video content | video |
| `<PDF>` | Display PDF documents (up to 100 pages) | PDF |
| `<HyperText>` | Display HTML content | HTML |
| `<Table>` | Display tabular data | table |
| `<TimeSeries>` | Display time series data | time series |
| `<List>` | Display list items | list |
| `<Paragraphs>` | Display paragraph text | paragraphs |
| `<Chat>` | Display conversational transcripts | JSON array |

**Common Object Tag parameters:**
- `name`: Element name (required)
- `value`: Data field reference (e.g., `$text`)

### 2. Control Tags (Add Annotations)
Tags that provide annotation tools for the displayed data.

#### Classification Tags

| Tag | Purpose | Use with |
|-----|---------|----------|
| `<Labels>` | Assign labels to regions (text, audio) | Text, Audio |
| `<Label>` | Single label value | child of Labels/RectangleLabels/etc |
| `<Choices>` | Single/multiple choice classification | Any data type |
| `<Choice>` | Single choice option | child of Choices/Taxonomy |
| `<Taxonomy>` | Hierarchical classification | Any data type |
| `<Rating>` | Numeric ratings | Any data type |

#### Region Annotation Tags

| Tag | Purpose | Use with |
|-----|---------|----------|
| `<RectangleLabels>` | Bounding boxes with labels | Image |
| `<PolygonLabels>` | Polygon regions with labels | Image |
| `<EllipseLabels>` | Ellipse regions with labels | Image |
| `<KeyPointLabels>` | Keypoint annotations | Image |
| `<BrushLabels>` | Semantic segmentation masks | Image |
| `<HyperTextLabels>` | HTML region labels | HyperText |
| `<ParagraphLabels>` | Paragraph region labels | Paragraphs |
| `<TimelineLabels>` | Time series segment labels | TimeSeries |
| `<TimeSeriesLabels>` | Time series classification | TimeSeries |

#### Region & Relation Tags

| Tag | Purpose |
|-----|---------|
| `<Rectangle>` | Bounding boxes without labels |
| `<Polygon>` | Polygon regions without labels |
| `<Ellipse>` | Ellipse regions without labels |
| `<KeyPoint>` | Keypoint annotations without labels |
| `<Brush>` | Segmentation masks without labels |
| `<Relations>` | Create relations between regions |
| `<Relation>` | Define relation type (child of Relations) |

#### Input Tags

| Tag | Purpose |
|-----|---------|
| `<TextArea>` | Text input for transcription/captioning |
| `<Number>` | Numeric input |

#### Scoring/Evaluation Tags

| Tag | Purpose |
|-----|---------|
| `<Ranker>` | Rank items by preference |
| `<Pairwise>` | Pairwise comparison |
| `<DateTime>` | Date/time input |

### 3. Visual & Experience Tags
Tags that modify the interface appearance and behavior.

| Tag | Purpose |
|-----|---------|
| `<View>` | Container for layout/styling (like HTML div) |
| `<Style>` | Apply CSS styles |
| `<Header>` | Add headers/titles |
| `<Filter>` | Filter data |
| `<Collapse>` | Collapsible sections |
| `<Markdown>` | Render markdown content |

## Common Patterns

### Text Classification
```xml
<View>
  <Choices name="sentiment" toName="text" choice="single">
    <Choice value="Positive" />
    <Choice value="Negative" />
    <Choice value="Neutral" />
  </Choices>
  <Text name="text" value="$text" />
</View>
```

### Named Entity Recognition (NER)
```xml
<View>
  <Labels name="ner" toName="text">
    <Label value="PER" background="red" />
    <Label value="ORG" background="orange" />
    <Label value="LOC" background="green" />
  </Labels>
  <Text name="text" value="$text" />
</View>
```

### Image Object Detection
```xml
<View>
  <RectangleLabels name="labels" toName="image">
    <Label value="Person" />
    <Label value="Vehicle" />
  </RectangleLabels>
  <Image name="image" value="$image" />
</View>
```

### Audio Transcription
```xml
<View>
  <Audio name="audio" value="$audio" />
  <TextArea name="transcription" toName="audio" />
</View>
```

### PDF Classification
```xml
<View>
  <PDF name="pdf" value="$pdf" />
  <Choices name="doc_type" toName="pdf">
    <Choice value="Legal" />
    <Choice value="Financial" />
    <Choice value="Technical" />
  </Choices>
</View>
```

### Chat Evaluation with LLM
```xml
<View>
  <Chat name="chat" value="$chat" llm="openai/gpt-4.1-nano" />
  <View visibleWhen="region-selected" whenRole="assistant">
    <Rating name="quality" toName="chat" perRegion="true" />
  </View>
</View>
```

### Relation Extraction
```xml
<View>
  <Relations>
    <Relation value="similar" />
    <Relation value="related" />
  </Relations>
  <Text name="text" value="$text" />
  <Labels name="labels" toName="text">
    <Label value="Entity" />
  </Labels>
</View>
```

## Key Parameters Reference

### Common Control Tag Parameters
- `toName`: Links control to object tag (required)
- `choice`: `"single"` | `"multiple"` - single/multi-select
- `perRegion`: Apply annotation to specific regions
- `required`: Validate that annotation is made
- `maxUsages`: Maximum uses per label

### Dynamic Labels/Choices
Load labels from task data:
```xml
<Choices name="choices" toName="text" value="$dynamic_labels" />
```

Task data:
```json
{
  "dynamic_labels": [
    {"value": "Label 1", "background": "red"},
    {"value": "Label 2"}
  ]
}
```

### Styling with Style Tag
```xml
<View>
  <Style>
    .fancy-border { border: 2px solid blue; padding: 20px; }
  </Style>
  <View className="fancy-border">
    <Header value="Styled Section" />
    <Text name="text" value="$text" />
  </View>
</View>
```

### Layout with View Tag
```xml
<View style="display: flex;">
  <View style="flex: 50%">
    <Text name="text1" value="$value1" />
    <Choices name="chc1" toName="text1">
      <Choice value="Option 1" />
    </Choices>
  </View>
  <View style="flex: 50%; margin-left: 1em">
    <Text name="text2" value="$value2" />
    <Rating name="rating" toName="text2" />
  </View>
</View>
```

### Conditional Visibility
Show/hide elements based on selections:
```xml
<View visibleWhen="choice-selected" whenTagName="sentiment" whenChoiceValue="Positive,Negative">
  <Header value="Please explain:" />
  <TextArea name="explanation" toName="text" />
</View>
```

## When to Read References

### references/tags-object.md
Read when working with specific object tags (Audio, Chat, PDF, Video, etc.) for detailed parameters and examples.

### references/tags-control.md
Read when implementing control tags for detailed parameter documentation and advanced configurations.

### references/tags-visual.md
Read when styling interfaces, implementing conditional visibility, or customizing layouts.

### references/templates.md
Read for complete template examples organized by task type (NLP, Computer Vision, Audio, etc.).

## External Documentation

For the most up-to-date documentation:
- **Tags Reference**: https://labelstud.io/tags/
- **Template Gallery**: https://labelstud.io/templates/
- **API Reference**: https://api.labelstud.io/
