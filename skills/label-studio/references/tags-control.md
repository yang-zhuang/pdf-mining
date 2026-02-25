# Control Tags - Detailed Reference

Control tags provide annotation tools for displayed data. All control tags require `toName` parameter linking to an object tag.

## Classification Tags

### Choices

Create multiple choice selections (radio buttons or checkboxes).

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of data element to label
- `choice` (default="single"): "single" | "multiple" | "single-radio"
- `showInline` (default="false"): Show in same visual line
- `required` (default="false"): Validate selection made
- `requiredMessage`: Message on validation failure
- `visibleWhen`: "region-selected", "no-region-selected", "choice-selected", "choice-unselected"
- `whenTagName`: Narrow visibility by tag name
- `whenLabelValue`: Narrow by label value (comma-separated)
- `whenChoiceValue`: Narrow by choice value (comma-separated)
- `perRegion`: Apply choice to specific region
- `perItem`: Apply to specific items in object
- `value`: Task data field with dynamic choices
- `layout`: "select" (dropdown), "inline" (horizontal), "vertical" (stacked)

**Example - Single choice:**
```xml
<Choices name="sentiment" toName="text" choice="single">
  <Choice value="Positive" />
  <Choice value="Negative" />
  <Choice value="Neutral" />
</Choices>
```

**Example - Dynamic choices:**
```xml
<Choices name="transcription" toName="audio" value="$variants" />
```

Task data:
```json
{
  "variants": [
    {"value": "Option 1", "html": "<img src='logo.png'>"},
    {"value": "Option 2"}
  ]
}
```

---

### Labels

Assign labels to regions (text, audio).

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of element to label
- `choice` (default="multiple"): "single" or "multiple"
- `maxUsages`: Maximum uses per label
- `showInline` (default="true"): Show in same line
- `opacity` (default="0.6"): Highlight opacity
- `fillColor`: Fill color (hex)
- `strokeColor` (default="#f48a42"): Stroke color (hex)
- `strokeWidth` (default="1"): Stroke width
- `value`: Task data field with dynamic labels

**Example - Text NER:**
```xml
<Labels name="ner" toName="text">
  <Label value="PER" background="red" />
  <Label value="ORG" background="orange" />
  <Label value="LOC" background="green" />
</Labels>
<Text name="text" value="$text" />
```

---

### Label

Single label value. Used as child of Labels, RectangleLabels, etc.

**Parameters:**
- `value` (required): Label value
- `alias`: Alternative identifier
- `background`: Background color (hex)
- `selectedColor`: Selected state color (hex)
- `showAlias` (default="false"): Show alias instead of value

---

### Taxonomy

Hierarchical classification with nested choices.

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of element to classify
- `apiUrl`: Beta - Retrieve taxonomy from remote source
- `leafsOnly` (default="false"): Only allow leaf node selection
- `showFullPath` (default="false"): Show full path of selected items
- `pathSeparator` (default="/"): Path separator
- `maxUsages`: Maximum uses per choice
- `maxWidth`/`minWidth`: Dropdown width
- `required` (default="false"): Require at least one option
- `placeholder`: Input prompt text
- `perRegion`/`perItem`: Apply to specific regions/items
- `labeling`: Use to label text regions (Text/HyperText only)
- `legacy`: Enable legacy version (allows adding labels, disables apiUrl)

**Example - Nested taxonomy:**
```xml
<Taxonomy name="media" toName="text">
  <Choice value="Online">
    <Choice value="UGC" />
    <Choice value="Free" />
    <Choice value="Paywall">
      <Choice value="NY Times" />
      <Choice value="WSJ" />
    </Choice>
  </Choice>
  <Choice value="Offline" />
</Taxonomy>
```

---

### Rating

Numeric rating selection.

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of element to rate
- `maxRating` (default="5"): Maximum rating value
- `defaultValue` (default="0"): Default rating
- `size` (default="medium"): "small", "medium", "large"
- `hotkey`: Hotkey for changing rating
- `required` (default="false"): Require rating
- `requiredMessage`: Message on validation failure
- `perRegion`/`perItem`: Rate specific regions/items

**Example:**
```xml
<Rating name="quality" toName="text" maxRating="10" />
```

---

## Region Annotation Tags

### RectangleLabels

Labeled bounding boxes for images.

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of image to label
- `choice` (default="multiple"): "single" or "multiple"
- `maxUsages`: Maximum uses per label
- `showInline` (default="true"): Show labels inline
- `opacity` (default="0.6"): Fill opacity
- `fillColor`/`strokeColor`: Colors (hex)
- `strokeWidth` (default="1"): Stroke width
- `canRotate` (default="true"): Show rotation control
- `snap`: "pixel" or "none"

**Result format:**
```json
{
  "original_width": 1920,
  "original_height": 1280,
  "image_rotation": 0,
  "value": {
    "x": 3.1,
    "y": 8.2,
    "width": 20,
    "height": 16,
    "rectanglelabels": ["Car"]
  }
}
```

---

### PolygonLabels

Labeled polygon regions for images.

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of image to label
- Similar styling parameters to RectangleLabels

---

### EllipseLabels

Labeled ellipse regions for images.

**Parameters:**
- Similar to RectangleLabels

---

### KeyPointLabels

Labeled keypoints for images.

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of image to label
- `maxUsages`: Maximum uses per label
- Similar styling parameters

---

### BrushLabels

Labeled semantic segmentation masks.

**Parameters:**
- `name` (required): Element name
- `toName` (required): Name of image to label
- `maxUsages`: Maximum uses per label

---

## Region Tags (Without Labels)

### Rectangle, Polygon, Ellipse, KeyPoint, Brush

Same functionality as *Labels variants but without automatic label assignment.

---

## Relations

### Relations

Container for defining relations between regions.

### Relation

Single relation type definition.

**Parameters:**
- `value` (required): Relation value
- `background`: Active label background color (hex)

**Example:**
```xml
<Relations>
  <Relation value="similar" />
  <Relation value="related" />
</Relations>
<Text name="text" value="$text" />
<Labels name="labels" toName="text">
  <Label value="Entity" />
</Labels>
```

---

## Input Tags

### TextArea

Text input field for transcription, captioning, etc.

**Parameters:**
- `name` (required): Element name
- `toName`: Name of object being labeled
- `value`: Pre-filled default value
- `placeholder`: Placeholder text
- `maxSubmissions`: Maximum submissions
- `editable` (default="false"): Show edit icon
- `transcription` (default="false"): Always keep editable
- `skipDuplicates` (default="false"): Prevent duplicate values
- `displayMode` (default="tag"): "tag" or "region-list"
- `rows` (default="1"): Number of rows
- `required` (default="false"): Require content
- `showSubmitButton`: Show/hide Add button
- `perRegion`/`perItem`: Apply to specific regions/items

**Example - Basic:**
```xml
<TextArea name="caption" toName="image" />
```

**Example - Region list (for OCR):**
```xml
<TextArea name="transcription" toName="image" perRegion="true" displayMode="region-list" />
```

---

### Number

Numeric input field.

**Parameters:**
- `name` (required): Element name
- `toName`: Name of object being labeled
- `value`: Default value
- `placeholder`: Placeholder text
- `required` (default="false"): Require input

---

## Scoring/Evaluation Tags

### Ranker

Rank items by preference.

**Parameters:**
- `name` (required): Element name
- `toName`: Name of element to rank

---

### Pairwise

Pairwise comparison between items.

**Parameters:**
- `name` (required): Element name
- `toName`: Name of element to compare

---

### DateTime

Date/time input.

**Parameters:**
- `name` (required): Element name
- `toName`: Name of object to tag
- `format`: Date format string
- `required` (default="false"): Require selection
