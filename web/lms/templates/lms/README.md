## HTML Render Structure

```
| base.html 
| __ project.html
|
| __ parcel.html
|    | __ owner_relationship.html
|
| __ owner.html
|    | __ owner_files.html
|    | __ owner_correspondence.html
|    | __ history.html
|    | __ owner_reminders.html
|    | __ owner_tasks.html
|    | __ owner_notes.html
```

## Save Response Container after Form Submit
Since POST response might return a new html with updated data, we want to render with new html. Usually `data-container-content` are also the ones initially get rendered from GET response.
```html
<div id="REMINDERS_VIEW" data-container="reminders">
  <div id="REMINDERS_CONTENT" data-container-content="reminders">
    ...
    <button>Open modal form</button>
  </div>
</div>
```

Response from POST method will be rendered into `data-container-content`

## How the form populate to modify

data-field: name has to be exact in the form

data-value: value of the field

```html
<div class='form-data'>
  <span data-field="" data value=""> </span>
</div>
```

## Tooltip for Dropdown Button

Change tooltip title with 'Close' prefix with dropdown opened
```html
<div class="dropdown">
  <button class="tooltip-wrap" data-bs-toggle="dropdown">
    Button Name
    <div class="tooltip">
      <span class="tooltip-action" title="View" titleOnClose="Close"> </span> Tooltip Title
    </div>
  </button>
</div>
```