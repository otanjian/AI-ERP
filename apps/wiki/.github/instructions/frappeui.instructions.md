---
applyTo: '**/*.vue'
---
---
applyTo: '**/*.vue'
---

###  General Backend API Calls

```vue
<template>
  <Button @click="todos.reload()" :loading="todos.loading"> Reload </Button>
  <pre>{{ todos }}</pre>
</template>

<script setup>
import { createResource } from 'frappe-ui'
let todos = createResource({
  url: '/api/method/frappe.client.get_list',
  params: {
    doctype: 'ToDo',
    filters: {
      allocated_to: 'faris@frappe.io',
    },
  },
})
todos.fetch() // GET request

// POST request
todos.submit({
  "description": "New ToDo",
})
</script>
```

### Document Resource

```vue
<script setup>
let todo = createDocumentResource({
  // name of the doctype
  doctype: 'ToDo',

  // name of the record
  name: '',

  // define doc methods to use as resources
  whitelistedMethods: {
    sendEmail: 'send_email',
  },
  // the above configuration enables the following API
  // todo.sendEmail.submit()

  // events
  // error can occur from failed request
  onError(error) {},
  // on successful response
  onSuccess(data) {},
  // transform data before setting it
  transform(doc) {
    doc.open = false
    return doc
  },
  // other events
  delete: {
    onSuccess() {},
    onError() {},
  },
  setValue: {
    onSuccess() {},
    onError() {},
  },
})

</script>
```

Example API:

```vue
todo.doc // doc returned from request
todo.reload() // reload the doc

// update options
todo.update({
  doctype: '',
  name: ''
})

todo.get // doc resource
todos.get.loading // true when data is being fetched
todos.get.error // error that occurred from making the request
todos.get.promise // promise object of the request, can be awaited

// resource to set value(s) on the document
todos.setValue
todos.setValue.submit({
    // field value pairs to set
    status: 'Closed',
    description: 'Updated description'
})

// same as setValue but debounced
todos.setValueDebounced
// will run once after 500ms
todos.setValueDebounced.submit({
    description: 'Updated description'
})

// resource to delete the document
todos.delete
todos.delete.submit()

// if whitelistedMethods is defined
// you get a resource for each whitelisted method
todos.sendEmail
todos.sendEmail.submit
todos.sendEmail.loading
```

### List Resource

List Resource is a wrapper on top of [Resource](./Resource.story.md) for working
with lists. This feature only works with a Frappe Framework backend as of now.

## Usage

A list resource knows how to fetch records of a DocType from a Frappe Framework
backend so there is no need to specify the url. Instead you only define
`doctype`, `fields`, `filters`, etc. You also get methods like `next()`,
`setValue()`, etc.

```vue
<template>
  <div class="space-y-4">
    <div
      class="flex items-center justify-between"
      v-for="todo in todos.data"
      :key="todo.name"
    >
      <div>
        {{ todo.description }}
      </div>
      <Badge>{{ todo.status }}</Badge>
    </div>
  </div>
  <Button @click="todos.next()"> Next Page </Button>
</template>
<script setup>
import { useList } from 'frappe-ui'
let todos = useList({
  doctype: 'ToDo',
  fields: ['name', 'description', 'status'],
  orderBy: 'creation desc',
  start: 0,
  pageLength: 5,
})
todos.fetch()
</script>
```

## Options API

You can also define resources if you are using Options API. You need to register
the `resourcesPlugin` first.

**main.js**

```js
import { resourcesPlugin } from 'frappe-ui'
app.use(resourcesPlugin)
```

In your .vue file, you can declare all your resources under the resources key as
functions. The resource object will be available on `this.$resources.[name]`. In
the following example, `this.$resources.todos` is the resource object.

**Component.vue**

```vue
<script>
export default {
  resources: {
    todos() {
      return {
        type: 'list',
        doctype: 'ToDo',
        fields: ['name', 'description', 'status'],
        orderBy: 'creation desc',
        start: 0,
        pageLength: 5,
        auto: true,
      }
    },
  },
}
</script>
```

## List of Options and API

Here is the list of all options and APIs that are available on a list resource.

### Options

```js
let todos = uesList({
    // name of the doctype
    doctype: 'ToDo',

    // list of fields
    fields: ['name', 'description', 'status', ...],

    // object of filters to apply
    filters: {
        status: 'Open'
    },

    // the order in which records must be sorted
    orderBy: 'creation desc',

    // index from which records should be fetched
    // default value is 0
    start: 0,

    // number of records to fetch in a single request
    // default value is 20
    pageLength: 20,

    // parent doctype when you are fetching records of a child doctype
    parent: null,

    // set to 1 to enable debugging of list query
    debug: 0,

    // cache key to cache the resource
    // can be a string
    cacheKey: 'todos',
    // or an array that can be serialized
    cacheKey: ['todos', 'faris@frappe.io'],

    // default value for url is "frappe.client.get_list"
    // specify url if you want to use a custom API method
    url: 'todo_app.api.get_todos',

    // make the first request automatically
    auto: true,

    // events
    // error can occur from failed request
    onError(error) {

    },
    // on successful response
    onSuccess(data) {

    },
    // transform data before setting it
    transform(data) {
      for (let d of data) {
        d.open = false
      }
      return data
    },
    // other events
    fetchOne: {
        onSuccess() {},
        onError() {}
    },
    insert: {
        onSuccess() {},
        onError() {}
    },
    delete: {
        onSuccess() {},
        onError() {}
    },
    setValue: {
        onSuccess() {},
        onError() {}
    },
    runDocMethod: {
        onSuccess() {},
        onError() {}
    },
})
```

### API

A list resource is made up of multiple individual resources. In our running
example, the resource object that fetches the list is at `todos.list`. So all
the [properties of a resource](./Resource.story.md) are available on this
object. Similarly, there are resources for `fetchOne`, `setValue`, `insert`,
`delete`, and `runDocMethod`.

```js
let todos = useList({...})

todos.data // data returned from request
todos.originalData // response data before being transformed
todos.reload() // reload the existing list
todos.next() // fetch the next page
todos.hasNextPage // whether there is next page to fetch

// update list options
todos.update({
  fields: ['*'],
  filters: {
    status: 'Closed'
  }
})

todos.data // list resource
todos.loading // true when data is being fetched
todos.error // error that occurred from making the request
todos.promise // promise object of the request, can be awaited

// resource to fetch and update a single record in the list
todos.fetchOne
// pass the name of the record to fetch that record and update the list
todos.fetchOne.submit(name)

// resource to set value(s) for a single record in the list
todos.setValue
todos.setValue.submit({
    // id of the record
    name: '',
    // field value pairs to set
    status: 'Closed',
    description: 'Updated description'
})

// resource to insert a new record in the list
todos.insert
todos.insert.submit({
    description: 'New todo'
})

// resource to delete a single record
todos.delete
todos.delete.submit(name)

// resource to run a doc method
todos.runDocMethod
todos.runDocMethod.submit({
    // name of the doc method
    method: 'send_email',
    // name of the record
    name: '',
    // params to pass to the method
    email: 'test@example.com'
})
```


### List View Component

### Story

```vue
<script setup>
import { reactive, h, ref } from 'vue'
import Avatar from '../Avatar/Avatar.vue'
import Badge from '../Badge/Badge.vue'
import { Button } from '../Button'
import FeatherIcon from '../FeatherIcon.vue'
import ListHeader from './ListHeader.vue'
import ListHeaderItem from './ListHeaderItem.vue'
import ListRow from './ListRow.vue'
import ListRowItem from './ListRowItem.vue'
import ListRows from './ListRows.vue'
import ListSelectBanner from './ListSelectBanner.vue'
import ListView from './ListView.vue'

const state = reactive({
  selectable: true,
  showTooltip: true,
  resizeColumn: true,
  emptyState: {
    title: 'No records found',
    description: 'Create a new record to get started',
    button: {
      label: 'New Record',
      variant: 'solid',
      onClick: () => console.log('New Record'),
    },
  },
})

const simple_columns = reactive([
  {
    label: 'Name',
    key: 'name',
    width: 3,
    getLabel: ({ row }) => row.name,
    prefix: ({ row }) => {
      return h(Avatar, {
        shape: 'circle',
        image: row.user_image,
        size: 'sm',
      })
    },
  },
  {
    label: 'Email',
    key: 'email',
    width: '200px',
  },
  {
    label: 'Role',
    key: 'role',
  },
  {
    label: 'Status',
    key: 'status',
  },
])

const simple_rows = [
  {
    id: 1,
    name: 'John Doe',
    email: 'john@doe.com',
    status: 'Active',
    role: 'Developer',
    user_image: 'https://avatars.githubusercontent.com/u/499550',
  },
  {
    id: 2,
    name: 'Jane Doe',
    email: 'jane@doe.com',
    status: 'Inactive',
    role: 'HR',
    user_image: 'https://avatars.githubusercontent.com/u/499120',
  },
]

const group_columns = reactive([
  {
    label: 'Name',
    key: 'name',
    width: 3,
  },
  {
    label: 'Email',
    key: 'email',
    width: '200px',
  },
  {
    label: 'Role',
    key: 'role',
  },
  {
    label: 'Status',
    key: 'status',
  },
])

const grouped_rows = ref([
  {
    group: 'Developer',
    collapsed: false,
    rows: [
      {
        id: 2,
        name: 'Gary Fox',
        email: 'gary@fox.com',
        status: 'Inactive',
        role: 'Developer',
      },
      {
        id: 6,
        name: 'Emily Davis',
        email: 'emily@davis.com',
        status: 'Active',
        role: 'Developer',
      },
      {
        id: 9,
        name: 'David Lee',
        email: 'david@lee.com',
        status: 'Inactive',
        role: 'Developer',
      },
    ],
  },
  {
    group: 'Manager',
    collapsed: false,
    rows: [
      {
        id: 3,
        name: 'John Doe',
        email: 'john@doe.com',
        status: 'Active',
        role: 'Manager',
      },
      {
        id: 8,
        name: 'Sarah Wilson',
        email: 'sarah@wilson.com',
        status: 'Active',
        role: 'Manager',
      },
    ],
  },
  {
    group: 'Designer',
    collapsed: false,
    rows: [
      {
        id: 4,
        name: 'Alice Smith',
        email: 'alice@smith.com',
        status: 'Active',
        role: 'Designer',
      },
      {
        id: 10,
        name: 'Olivia Taylor',
        email: 'olivia@taylor.com',
        status: 'Active',
        role: 'Designer',
      },
    ],
  },
  {
    group: 'HR',
    collapsed: false,
    rows: [
      {
        id: 1,
        name: 'Jane Mary',
        email: 'jane@doe.com',
        status: 'Inactive',
        role: 'HR',
      },
      {
        id: 7,
        name: 'Michael Brown',
        email: 'michael@brown.com',
        status: 'Inactive',
        role: 'HR',
      },
      {
        id: 12,
        name: 'Sophia Martinez',
        email: 'sophia@martinez.com',
        status: 'Active',
        role: 'HR',
      },
    ],
  },
  {
    group: 'Tester',
    collapsed: false,
    rows: [
      {
        id: 5,
        name: 'Bob Johnson',
        email: 'bob@johnson.com',
        status: 'Inactive',
        role: 'Tester',
      },
      {
        id: 11,
        name: 'James Anderson',
        email: 'james@anderson.com',
        status: 'Inactive',
        role: 'Tester',
      },
    ],
  },
])

const custom_columns = reactive([
  {
    label: 'Name',
    key: 'name',
    width: 3,
    icon: 'user',
  },
  {
    label: 'Email',
    key: 'email',
    width: '200px',
    icon: 'at-sign',
  },
  {
    label: 'Role',
    key: 'role',
    icon: 'users',
  },
  {
    label: 'Status',
    key: 'status',
    icon: 'check-circle',
  },
])

const custom_rows = [
  {
    id: 1,
    name: {
      label: 'John Doe',
      image: 'https://avatars.githubusercontent.com/u/499550',
    },
    email: 'john@doe.com',
    status: {
      label: 'Active',
      bg_color: 'bg-surface-green-3',
    },
    role: {
      label: 'Developer',
      color: 'green',
    },
  },
  {
    id: 2,
    name: {
      label: 'Jane Doe',
      image: 'https://avatars.githubusercontent.com/u/499120',
    },
    email: 'jane@doe.com',
    status: {
      label: 'Inactive',
      bg_color: 'bg-surface-red-5',
    },
    role: {
      label: 'HR',
      color: 'red',
    },
  },
]
</script>

<template>
  <Story :layout="{ type: 'grid', width: '95%' }">
    <Variant title="Simple List">
      <ListView
        class="h-[150px]"
        :columns="simple_columns"
        :rows="simple_rows"
        :options="{
          getRowRoute: (row) => ({ name: 'User', params: { userId: row.id } }),
          selectable: state.selectable,
          showTooltip: state.showTooltip,
          resizeColumn: state.resizeColumn,
        }"
        row-key="id"
      />
    </Variant>
    <Variant title="Custom List">
      <ListView
        class="h-[150px]"
        :columns="custom_columns"
        :rows="custom_rows"
        :options="{
          onRowClick: (row) => console.log(row),
          selectable: state.selectable,
          showTooltip: state.showTooltip,
          resizeColumn: state.resizeColumn,
        }"
        row-key="id"
      >
        <ListHeader>
          <ListHeaderItem
            v-for="column in custom_columns"
            :key="column.key"
            :item="column"
          >
            <template #prefix="{ item }">
              <FeatherIcon :name="item.icon" class="h-4 w-4" />
            </template>
          </ListHeaderItem>
        </ListHeader>
        <ListRows>
          <ListRow
            v-for="row in custom_rows"
            :key="row.id"
            v-slot="{ column, item }"
            :row="row"
          >
            <ListRowItem :item="item" :align="column.align">
              <template #prefix>
                <div
                  v-if="column.key == 'status'"
                  class="h-3 w-3 rounded-full"
                  :class="item.bg_color"
                />
                <Avatar
                  v-if="column.key == 'name'"
                  :shape="'circle'"
                  :image="item.image"
                  size="sm"
                />
              </template>
              <Badge
                v-if="column.key == 'role'"
                variant="subtle"
                :theme="item.color"
                size="md"
                :label="item.label"
              />
            </ListRowItem>
          </ListRow>
        </ListRows>
        <ListSelectBanner>
          <template #actions="{ unselectAll }">
            <div class="flex gap-2">
              <Button variant="ghost" label="Delete" />
              <Button
                variant="ghost"
                label="Unselect all"
                @click="unselectAll"
              />
            </div>
          </template>
        </ListSelectBanner>
      </ListView>
    </Variant>
    <Variant title="Grouped Rows">
      <ListView
        class="h-[250px]"
        :columns="group_columns"
        :rows="grouped_rows"
        :options="{
          getRowRoute: (row) => ({ name: 'User', params: { userId: row.id } }),
          selectable: state.selectable,
          showTooltip: state.showTooltip,
          resizeColumn: state.resizeColumn,
        }"
        row-key="id"
      >
        <template #group-header="{ group }">
          <span class="text-base font-medium leading-6 text-ink-gray-9">
            {{ group.group }} ({{ group.rows.length }})
          </span>
        </template>
      </ListView>
    </Variant>
    <Variant title="Cell Slot">
      <div>
        <ListView
          class="h-[250px]"
          :columns="simple_columns"
          :rows="simple_rows"
          :options="{
            selectable: state.selectable,
            showTooltip: state.showTooltip,
            resizeColumn: state.resizeColumn,
            emptyState: state.emptyState,
          }"
          row-key="id"
        >
          <template #cell="{ item, row, column }">
            <Badge v-if="column.key == 'status'">{{ item }}</Badge>
            <span class="font-medium text-ink-gray-7" v-else>{{ item }}</span>
          </template>
        </ListView>
      </div>
    </Variant>
    <Variant title="Empty List">
      <div>
        <ListView
          class="h-[250px]"
          :columns="simple_columns"
          :rows="[]"
          :options="{
            selectable: state.selectable,
            showTooltip: state.showTooltip,
            resizeColumn: state.resizeColumn,
            emptyState: state.emptyState,
          }"
          row-key="id"
        />
      </div>
    </Variant>

    <template #controls>
      <HstCheckbox v-model="state.selectable" title="Selectable" />
      <HstCheckbox v-model="state.showTooltip" title="Show tooltip" />
      <HstCheckbox v-model="state.resizeColumn" title="Resize Column" />
      <!-- empty state config -->
      <HstText
        v-model="state.emptyState.title"
        title="Empty Title"
        placeholder="No records found"
      />
      <HstText
        v-model="state.emptyState.description"
        title="Empty Description"
        placeholder="Create a new record to get started"
      />
    </template>
  </Story>
</template>
```

## Props

### Row Key

`row-key` is a unique key which is used to identify each row in the list. It is
required to be passed in the `row` object.

### Column

1. `label` & `key` is required in column object.

2. `width` is optional and it is used to set column width in list

   1. If you need a column to be `3` times a default column then add `3`. if
      width is not mentioned default will be `1`
   2. You can also add custom width in px and rem e.g `300px` or `12rem`
   3. Combination of both can also be used.

3. `align` is also optional. You can change the alignment of the content in the
   column by setting it as.

   1. `start` or `left` (default)
   2. `center` or `middle`
   3. `end` or `right`

4. You can add more attributes which can be used to render custom column header
   items.

### Row

1. The row object must contain a unique_key which was mentioned in ListView
   `row-key`
2. Then you can add the row fields as key value pairs and each field can be an
   object or a string (to handle custom rendering)

   ```
   {
   	// unique_key 'id'
   	id: 1,

   	// row fields
   	name: 'John Doe',
   	age: 25,
   	email: 'john@doe.com',
   }
   ```

   E.g field value as an object (to handle custom rendering), but make sure it
   has a `label` attribute which holds the actual value to be shown

   ```
   row: {
   	name: {
   		label: 'John Doe',
   		image: '/johndoe.jpg',
   	},
   	age: 25,
   	status: {
   		label: 'Active',
   		color: 'green'
   	}
   }
   ```

### Grouped Rows

To render grouped rows, you must provide `rows` in the following format:

```
[
    {
        group: 'Group Title 1',
        collapsed: false,
        rows: [
            {id: 1, key1: value1, key2: value2, ...},
            {id: 2, key1: value1, key2: value2, ...},
        ]
    },
    {
        group: 'Group Title 2',
        collapsed: false,
        rows: [
            {id: 3, key1: value1, key2: value2, ...},
            {id: 4, key1: value1, key2: value2, ...},
        ]
    },
]
```

### Options

1. If you want to route using router-link just add a `getRowRoute` function
   which returns a route object

   `getRowRoute: (row) => ({ name: 'User', params: { userId: row.id } })`

2. if you need to do some action add a `onRowClick` event handler

   `onRowClick: (row) => console.log(row.label + ' was clicked')`

3. selectable (Boolean) - if true, checkbox will be shown in header and rows, to
   select/multiselect rows and perform some action on them - default is true
4. showTooltip (Boolean) - if true, tooltip will be shown on hover of row -
   default is true
5. resizeColumn (Boolean) - if true, column can be resized by dragging the
   resizer on the right side of the column header - default is false

---

### Selection Banner (Will be shown when selectable (default is true) is true)

**Without custom action buttons:**
<img width="1213" alt="image" src="https://github.com/frappe/frappe-ui/assets/30859809/36fafcf5-45c6-43f0-acde-f64afe38b550">

**With custom action buttons:**
<img width="1212" alt="image" src="https://github.com/frappe/frappe-ui/assets/30859809/55e751b2-df66-4ff0-b852-af463014463f">

```
<ListSelectBanner>
	<template #actions>
	  <div class="flex gap-2">
	    <Button variant="ghost" label="Delete" />
	    <Button variant="ghost" label="Edit" />
	  </div>
	</template>
</ListSelectBanner>
```

You can also make your own custom selection banner

<img width="629" alt="image" src="https://github.com/frappe/frappe-ui/assets/30859809/38dfa834-96a2-4ac5-ad4b-30b3e6871d3f">

```
<ListSelectBanner>
	<div>Custom Banner</div>
</ListSelectBanner>
```


### Badge Component

#### Story

```vue
<script setup lang="ts">
import { reactive } from 'vue'
import Badge from './Badge.vue'
const state = reactive({
  theme: 'gray',
  size: 'sm',
  label: 'Badge',
})
const variants = ['solid', 'subtle', 'outline', 'ghost']
const themes = ['gray', 'blue', 'green', 'orange', 'red']
const sizes = ['sm', 'md', 'lg']
</script>

<template>
  <Story :layout="{ type: 'grid', width: 300 }">
    <Variant v-for="variant in variants" :key="variant" :title="variant">
      <Badge :variant="variant" v-bind="state">{{ state.label }}</Badge>
    </Variant>

    <template #controls>
      <HstText v-model="state.label" title="Content" />
      <HstSelect v-model="state.theme" :options="themes" title="Theme" />
      <HstSelect v-model="state.size" :options="sizes" title="Size" />
    </template>
  </Story>
</template>
```


### FormControl Component


#### Story

```vue
<script setup lang="ts">
import { reactive, ref } from 'vue'
import FormControl from './FormControl.vue'
import FeatherIcon from '../FeatherIcon.vue'
import { Avatar } from '../Avatar'

const state = reactive({
  size: 'sm',
  variant: 'subtle',
  placeholder: 'Placeholder',
  disabled: false,
  label: 'Label',
})
const inputValue = ref('')
const selectValue = ref(null)
const autocompleteValue = ref(null)
const checkboxValue = ref(false)

const inputTypes = [
  'text',
  'number',
  'email',
  'date',
  'password',
  'search',
  'textarea',
]
const sizes = ['sm', 'md', 'lg', 'xl']
const variants = ['subtle', 'outline']
</script>

<template>
  <Story :layout="{ type: 'grid', width: 500 }">
    <Variant
      v-for="inputType in inputTypes"
      :key="inputType"
      :title="inputType"
    >
      <div class="p-2">
        <FormControl :type="inputType" v-bind="state" v-model="inputValue" />
      </div>
    </Variant>
    <Variant title="select">
      <div class="p-2">
        <FormControl
          type="select"
          :options="[
            { label: 'One', value: '1' },
            { label: 'Two', value: '2' },
            { label: 'Three', value: '3' },
          ]"
          v-bind="state"
          v-model="selectValue"
        />
      </div>
    </Variant>
    <Variant title="autocomplete">
      <div class="p-2">
        <FormControl
          type="autocomplete"
          :options="[
            { label: 'One', value: '1' },
            { label: 'Two', value: '2' },
            { label: 'Three', value: '3' },
          ]"
          v-bind="state"
          v-model="autocompleteValue"
        />
      </div>
    </Variant>
    <Variant title="checkbox">
      <div class="p-2">
        <FormControl type="checkbox" v-bind="state" v-model="checkboxValue" />
      </div>
    </Variant>

    <Variant title="prefix slot icon">
      <div class="p-2">
        <FormControl type="text" label="Label">
          <template #prefix>
            <FeatherIcon class="w-4" name="search" />
          </template>
        </FormControl>
      </div>
    </Variant>

    <Variant title="suffix slot icon">
      <div class="p-2">
        <FormControl type="text" label="Label">
          <template #suffix>
            <FeatherIcon class="w-4" name="search" />
          </template>
        </FormControl>
      </div>
    </Variant>

    <Variant title="prefix slot avatar">
      <div class="p-2">
        <FormControl type="text" label="Label">
          <template #prefix>
            <Avatar
              size="sm"
              image="https://avatars.githubusercontent.com/u/499550?s=60&v=4"
            />
          </template>
        </FormControl>
      </div>
    </Variant>

    <template #controls>
      <HstSelect v-model="state.variant" :options="variants" title="Variant" />
      <HstSelect v-model="state.size" :options="sizes" title="Size" />
    </template>
  </Story>
</template>
```


### Toasts

Example:

```vue
<script setup>
import { toast } from 'frappe-ui'

toast.success('Converted successfully')
toast.warning('Converted Pending')
toast.error('Conversion Failed')
</script>
```


### Dropdown Component

The icon is name of a lucide icon.

#### Story

```vue
<script setup lang="ts">
import { Dropdown } from './index'
import { Button } from '../Button'

const actions = [
  {
    label: 'Edit',
    icon: 'edit',
    onClick: () => console.log('Edit clicked'),
  },
  {
    label: 'Delete',
    icon: 'trash-2',
    theme: 'red',
    onClick: () => console.log('Delete clicked'),
  },
]

const groupedActions = [
  {
    group: 'Actions',
    items: [
      {
        label: 'Edit',
        icon: 'edit',
        onClick: () => console.log('Edit clicked'),
      },
      {
        label: 'Duplicate',
        icon: 'copy',
        onClick: () => console.log('Duplicate clicked'),
      },
      {
        label: 'More Actions',
        icon: 'more-horizontal',
        submenu: [
          {
            label: 'Archive',
            icon: 'archive',
            onClick: () => console.log('Archive clicked'),
          },
          {
            label: 'Export',
            icon: 'download',
            submenu: [
              {
                label: 'Export as PDF',
                icon: 'file-text',
                onClick: () => console.log('Export as PDF clicked'),
              },
              {
                label: 'Export as CSV',
                icon: 'file',
                onClick: () => console.log('Export as CSV clicked'),
              },
            ],
          },
          {
            label: 'Share',
            icon: 'share',
            onClick: () => console.log('Share clicked'),
          },
        ],
      },
    ],
  },
  {
    group: 'Danger',
    items: [
      {
        label: 'Delete',
        icon: 'trash-2',
        theme: 'red',
        onClick: () => console.log('Delete clicked'),
      },
    ],
  },
]

const submenuActions = [
  {
    label: 'New',
    icon: 'plus',
    submenu: [
      {
        group: 'Documents',
        items: [
          {
            label: 'New Document',
            icon: 'file-plus',
            onClick: () => console.log('New Document clicked'),
          },
          {
            label: 'New Template',
            icon: 'file-text',
            onClick: () => console.log('New Template clicked'),
          },
          {
            label: 'Delete',
            icon: 'trash-2',
            theme: 'red',
            onClick: () => console.log('Delete clicked'),
          },
        ],
      },
      {
        group: 'Organization',
        items: [
          {
            label: 'New Folder',
            icon: 'folder-plus',
            onClick: () => console.log('New Folder clicked'),
          },
          {
            label: 'New Project',
            icon: 'briefcase',
            onClick: () => console.log('New Project clicked'),
          },
        ],
      },
    ],
  },
  {
    label: 'Edit',
    icon: 'edit',
    onClick: () => console.log('Edit clicked'),
  },
  {
    label: 'Share',
    icon: 'share',
    submenu: [
      {
        label: 'Share with Link',
        icon: 'link',
        onClick: () => console.log('Share with Link clicked'),
      },
      {
        label: 'Share with Email',
        icon: 'mail',
        onClick: () => console.log('Share with Email clicked'),
      },
      {
        group: 'Advanced',
        items: [
          {
            label: 'Share Settings',
            icon: 'settings',
            onClick: () => console.log('Share Settings clicked'),
          },
          {
            label: 'Permission Management',
            icon: 'shield',
            onClick: () => console.log('Permission Management clicked'),
          },
        ],
      },
    ],
  },
]
</script>

<template>
  <Story title="Dropdown" :layout="{ type: 'grid', width: '200px' }">
    <Variant title="Default">
      <div class="asdf">
        <Dropdown :options="actions" />
      </div>
    </Variant>

    <Variant title="With Custom Button">
      <Dropdown :options="actions">
        <Button variant="solid">Custom Trigger</Button>
      </Dropdown>
    </Variant>

    <Variant title="With Groups">
      <Dropdown :options="groupedActions" />
    </Variant>

    <Variant title="Right Aligned">
      <Dropdown :options="actions" placement="right" />
    </Variant>

    <Variant title="Center Aligned">
      <Dropdown :options="actions" placement="center" />
    </Variant>

    <Variant title="With Submenus">
      <Dropdown :options="submenuActions" />
    </Variant>

    <Variant title="With Nested Submenus">
      <Dropdown :options="groupedActions" />
    </Variant>
  </Story>
</template>
```

### Dialog Component


#### Story

```vue
<script setup lang="ts">
import { ref } from 'vue'
import Dialog from './Dialog.vue'
import { Button } from '../Button'
import { Dropdown } from '../Dropdown'
import LucideSettings from '~icons/lucide/settings'
import LucideStar from '~icons/lucide/star'
import LucideChevronDown from '~icons/lucide/chevron-down'
import { Autocomplete } from '../Autocomplete'

const dialog1 = ref(false)
const dialog2 = ref(false)
const dialog3 = ref(false)
const dialog4 = ref(false)
const dialog5 = ref(false)
const dialog6 = ref(false)

// Dropdown state
const selectedOption = ref('Option 1')

const autocompleteValue = ref({ label: '', value: '' })

const dropdownOptions = [
  {
    label: 'Option 1',
    onClick: () => {
      selectedOption.value = 'Option 1'
    },
  },
  {
    label: 'Option 2',
    onClick: () => {
      selectedOption.value = 'Option 2'
    },
  },
  {
    label: 'Option 3',
    onClick: () => {
      selectedOption.value = 'Option 3'
    },
  },
  {
    group: 'Advanced Options',
    items: [
      {
        label: 'Advanced Option A',
        icon: LucideSettings,
        onClick: () => {
          selectedOption.value = 'Advanced Option A'
        },
      },
      {
        label: 'Advanced Option B',
        icon: LucideStar,
        onClick: () => {
          selectedOption.value = 'Advanced Option B'
        },
      },
    ],
  },
]

const createPromise = (): Promise<void> => {
  return new Promise((resolve) => {
    setTimeout(resolve, 2000)
  })
}
</script>

<template>
  <Story :layout="{ width: 500, type: 'grid' }">
    <!-- 1. Basic Dialog with Actions -->
    <Variant title="Basic Dialog with Actions" autoPropsDisabled>
      <Button @click="dialog1 = true">Show Confirmation Dialog</Button>
      <Dialog
        :options="{
          title: 'Confirm Action',
          message: 'Are you sure you want to proceed with this action?',
          size: 'lg',
          icon: {
            name: 'alert-triangle',
            appearance: 'warning',
          },
          actions: [
            {
              label: 'Confirm',
              variant: 'solid',
              onClick: () => createPromise(),
            },
          ],
        }"
        v-model="dialog1"
      />
    </Variant>

    <!-- 2. Custom Content with Slots -->
    <Variant title="Custom Content with Slots" autoPropsDisabled>
      <Button @click="dialog2 = true">Show Custom Dialog</Button>
      <Dialog v-model="dialog2">
        <template #body-title>
          <h3 class="text-2xl font-semibold text-blue-600">
            Custom Title with Styling
          </h3>
        </template>
        <template #body-content>
          <div class="space-y-4">
            <p class="text-gray-700">
              This dialog uses custom slots for flexible content layout.
            </p>
            <div class="bg-blue-50 p-4 rounded-lg">
              <p class="text-blue-800">
                You can put any content here including forms, lists, or other
                components.
              </p>
            </div>
          </div>
        </template>
        <template #actions="{ close }">
          <div class="flex justify-start flex-row-reverse gap-2">
            <Button variant="solid" @click="close">Save Changes</Button>
            <Button variant="outline" @click="close">Cancel</Button>
          </div>
        </template>
      </Dialog>
    </Variant>

    <!-- 3. Different Sizes -->
    <Variant title="Different Sizes" autoPropsDisabled>
      <div class="space-x-2">
        <Button @click="dialog3 = true">Small Dialog</Button>
        <Button @click="dialog4 = true">Large Dialog</Button>
      </div>

      <!-- Small Dialog -->
      <Dialog
        :options="{
          title: 'Small Dialog',
          message: 'This is a small dialog.',
          size: 'sm',
          actions: [{ label: 'OK', variant: 'solid' }],
        }"
        v-model="dialog3"
      />

      <!-- Large Dialog -->
      <Dialog
        :options="{
          title: 'Large Dialog',
          message: 'This is a large dialog with more space for content.',
          size: '4xl',
          actions: [{ label: 'OK', variant: 'solid' }],
        }"
        v-model="dialog4"
      />
    </Variant>

    <!-- 4. Disable Outside Click -->
    <Variant title="Disable Outside Click to Close" autoPropsDisabled>
      <Button @click="dialog5 = true">Show Modal Dialog</Button>
      <Dialog
        :options="{
          title: 'Modal Dialog',
          message:
            'This dialog cannot be closed by clicking outside. Use the buttons or ESC key.',
          actions: [{ label: 'Close', variant: 'solid' }],
        }"
        :disable-outside-click-to-close="true"
        v-model="dialog5"
      />
    </Variant>

    <!-- 5. Dialog with Interactive Components -->
    <Variant title="Dialog with Interactive Components" autoPropsDisabled>
      <Button @click="dialog6 = true">Show Settings Dialog</Button>
      <Dialog v-model="dialog6">
        <template #body-title>
          <h3 class="text-2xl font-semibold text-ink-gray-9">
            Settings Dialog
          </h3>
        </template>
        <template #body-content>
          <div class="space-y-6 text-base">
            <p class="text-gray-700">
              This dialog contains interactive elements to test proper layering.
            </p>

            <Autocomplete
              :options="[
                { label: 'Option A', value: 'A' },
                { label: 'Option B', value: 'B' },
                { label: 'Option C', value: 'C' },
              ]"
              placeholder="Type to search..."
              v-model="autocompleteValue"
            />

            <div class="space-y-3">
              <label class="block text-sm font-medium text-gray-700">
                Select an option:
              </label>
              <Dropdown :options="dropdownOptions" placement="left">
                <Button variant="outline">
                  {{ selectedOption }}

                  <template #suffix>
                    <LucideChevronDown class="h-4 w-4 text-gray-500" />
                  </template>
                </Button>
              </Dropdown>
            </div>

            <div class="bg-gray-50 text-p-sm p-4 text-ink-gray-6 rounded-lg">
              <p><strong>Selected value:</strong> {{ selectedOption }}</p>
              <p class="mt-1">
                Interactive components should work properly within dialogs.
              </p>
            </div>
          </div>
        </template>
        <template #actions="{ close }">
          <div class="flex space-x-2">
            <Button variant="solid" @click="close">Save Settings</Button>
            <Button variant="outline" @click="close">Cancel</Button>
          </div>
        </template>
      </Dialog>
    </Variant>
  </Story>
</template>
```

### Tab Component

Story: 


```vue
<script setup lang="ts">
import { h, reactive } from 'vue'
import Tabs from './Tabs.vue'
import FeatherIcon from '../FeatherIcon.vue'
const state = reactive({
  index: 0,
  tabs_without_icon: [
    {
      label: 'Github',
      content:
        'Github is a code hosting platform for version control and collaboration. It lets you and others work together on projects from anywhere.',
    },
    {
      label: 'Twitter',
      content:
        'Twitter is an American microblogging and social networking service on which users post and interact with messages known as "tweets".',
    },
    {
      label: 'Linkedin',
      content:
        'LinkedIn is an American business and employment-oriented online service that operates via websites and mobile apps.',
    },
  ],
  tabs_with_icon: [
    {
      label: 'Github',
      content:
        'Github is a code hosting platform for version control and collaboration. It lets you and others work together on projects from anywhere.',
      icon: h(FeatherIcon, { class: 'w-4 h-4', name: 'github' }),
    },
    {
      label: 'Twitter',
      content:
        'Twitter is an American microblogging and social networking service on which users post and interact with messages known as "tweets".',
      icon: h(FeatherIcon, { class: 'w-4 h-4', name: 'twitter' }),
    },
    {
      label: 'Linkedin',
      content:
        'LinkedIn is an American business and employment-oriented online service that operates via websites and mobile apps.',
      icon: h(FeatherIcon, { class: 'w-4 h-4', name: 'linkedin' }),
    },
  ],
})
</script>

<template>
  <Story :layout="{ type: 'grid', width: '80%' }">
    <Variant title="Without Icon">
      <Tabs
        as="div"
        class="border rounded"
        v-model="state.index"
        :tabs="state.tabs_without_icon"
      >
        <template #tab-panel="{ tab }">
          <div class="p-5">
            {{ tab.content }}
          </div>
        </template>
      </Tabs>
    </Variant>
    <Variant title="With Icon">
      <Tabs
        as="div"
        class="border rounded"
        v-model="state.index"
        :tabs="state.tabs_with_icon"
      >
        <template #tab-panel="{ tab }">
          <div class="p-5">
            {{ tab.content }}
          </div>
        </template>
      </Tabs>
    </Variant>
    <Variant title="Vertical Tabs">
      <Tabs
        as="div"
        class="border rounded"
        v-model="state.index"
        :tabs="state.tabs_with_icon"
        vertical
      >
        <template #tab-panel="{ tab }">
          <div class="p-5">
            {{ tab.content }}
          </div>
        </template>
      </Tabs>
    </Variant>

    <template #controls>
      <HstNumber v-model="state.index" title="Tab Index" />
    </template>
  </Story>
</template>

```
