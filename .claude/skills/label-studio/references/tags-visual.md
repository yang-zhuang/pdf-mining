# Visual & Experience Tags - Detailed Reference

Visual tags modify the interface appearance, layout, and user experience.

## View

Container element for layout and styling (similar to HTML div).

**Parameters:**
- `display`: "block" or "inline"
- `style`: CSS style string
- `className`: CSS class name (used with Style tag)
- `idAttr`: Unique ID for CSS targeting
- `visibleWhen`: "region-selected", "choice-selected", "no-region-selected", "choice-unselected"
- `whenTagName`: Narrow visibility by tag name
- `whenLabelValue`: Narrow by label value (comma-separated)
- `whenChoiceValue`: Narrow by choice value (comma-separated)

**Example - Flex layout:**
```xml
<View style="display: flex;">
  <View style="flex: 50%">
    <Header value="Left side" />
    <Text name="text1" value="$text1" />
  </View>
  <View style="flex: 50%; margin-left: 1em">
    <Header value="Right side" />
    <Text name="text2" value="$text2" />
  </View>
</View>
```

**Example - Conditional visibility (region selected):**
```xml
<View visibleWhen="region-selected" whenLabelValue="PER,ORG">
  <Header value="Selected: Person or Organization" />
  <TextArea name="note" toName="text" />
</View>
```

**Example - Conditional visibility (choice selected):**
```xml
<View visibleWhen="choice-selected" whenTagName="sentiment" whenChoiceValue="Positive,Negative">
  <Header value="Why?" />
  <TextArea name="explanation" toName="text" />
</View>
```

---

## Style

Apply CSS styles to interface elements.

**Parameters:**
- CSS class selector (`.className`) as direct child content
- CSS properties inside the class definition

**Example - Style specific element:**
```xml
<View>
  <Style>
    .fancy-border { border: 4px dotted blue; text-align: center; padding: 20px; }
  </Style>
  <View className="fancy-border">
    <Header value="Styled Section" />
    <Text name="text" value="$text" />
  </View>
</View>
```

**Example - Multiple styles:**
```xml
<Style>
  .header-red { background: #ff0000; color: white; }
  .choice-green { border: 2px solid green; }
</Style>
```

**Example - Modify default Label Studio classes:**
```xml
<Style>
  .ant-radio-wrapper { border: 2px solid green; }
</Style>
<Choices name="chc" toName="text" choice="single-radio">
  <Choice value="Option 1" />
  <Choice value="Option 2" />
</Choices>
```

**Common class names to style:**
- `.htx-label`: Label tags
- `.htx-choice`: Choice tags
- `.ant-radio-wrapper`: Radio buttons
- `.ant-checkbox-wrapper`: Checkboxes
- `.htx-textarea`: TextArea fields

---

## Header

Add headers/titles to the interface.

**Parameters:**
- `value` (required): Header text
- `size` (default="4"): Header size ("1" largest, "6" smallest)

**Example:**
```xml
<Header value="Instructions" size="3" />
```

---

## Filter

Filter displayed data based on criteria.

**Parameters:**
- `hotkey`: Hotkey to activate filter

---

## Collapse

Create collapsible/expandable sections.

**Parameters:**
- `value`: Section title

**Example:**
```xml
<Collapse value="Advanced Options">
  <Taxonomy name="taxonomy" toName="text">
    <!-- nested choices -->
  </Taxonomy>
</Collapse>
```

---

## Markdown

Render markdown content.

**Parameters:**
- `value`: Markdown content or data field reference

**Example:**
```xml
<Markdown value="# Instructions

Please read carefully..." />
```

**Example - From data:**
```xml
<Markdown value="$instructions" />
```

---

## Advanced Layout Patterns

### Two-column layout
```xml
<View style="display: flex; gap: 1rem;">
  <View style="flex: 1;">
    <Header value="Data" />
    <Text name="text" value="$text" />
  </View>
  <View style="flex: 1;">
    <Header value="Annotations" />
    <Labels name="labels" toName="text">
      <Label value="Entity" />
    </Labels>
  </View>
</View>
```

### Three-column layout
```xml
<View style="display: flex; gap: 1rem;">
  <View style="flex: 1;">
    <!-- Column 1 -->
  </View>
  <View style="flex: 1;">
    <!-- Column 2 -->
  </View>
  <View style="flex: 1;">
    <!-- Column 3 -->
  </View>
</View>
```

### Side panel (for chat evaluation)
```xml
<View style="display: flex; width: 100%;">
  <Chat name="chat" value="$chat" />
  <View style="flex: 300px 0 0; border-left: 2px solid #ccc; padding-left: 16px;">
    <Header value="Evaluation" />
    <Rating name="rating" toName="chat" />
  </View>
</View>
```

---

## Conditional Visibility Patterns

### Show when region selected (NER/region annotation)
```xml
<View visibleWhen="region-selected" whenLabelValue="PER,ORG">
  <Header value="Person or Organization selected" />
  <TextArea name="note" toName="text" />
</View>
```

### Show when choice selected
```xml
<View visibleWhen="choice-selected" whenTagName="sentiment" whenChoiceValue="Positive">
  <Header value="What makes this positive?" />
  <TextArea name="why" toName="text" />
</View>
```

### Show when no region selected
```xml
<View visibleWhen="no-region-selected">
  <Text name="hint" value="Select a region to see options" />
</View>
```

### Show for specific chat role
```xml
<View visibleWhen="region-selected" whenRole="assistant">
  <Rating name="assistant_quality" toName="chat" perRegion="true" />
</View>
```

---

## PDF-Specific Styling

```xml
<Style>
  .htx-pdf { height: calc(100vh - 250px); }
</Style>
```

---

## Responsive Design

Use percentages and flex for responsive layouts:
```xml
<View style="display: flex; flex-wrap: wrap;">
  <View style="flex: 1 1 300px;">
    <!-- Content, minimum 300px -->
  </View>
  <View style="flex: 1 1 300px;">
    <!-- Content, minimum 300px -->
  </View>
</View>
```
