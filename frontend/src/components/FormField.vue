<template>
  <div class="form-group">
    <label :for="fieldId" class="field-label">{{ label }}</label>
    <input v-if="type === 'text' || type === 'number'"
           :id="fieldId"
           :type="type"
           :placeholder="placeholder"
           :value="modelValue"
           @input="$emit('update:modelValue', $event.target.value)"
           class="input-field" />
    <select v-else-if="type === 'select'"
            :id="fieldId"
            :value="modelValue"
            @change="$emit('update:modelValue', $event.target.value)"
            class="select-field">
      <option v-for="option in options"
              :key="option.value"
              :value="option.value">
        {{ option.label }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Option {
  label: string
  value: string
}

const props = defineProps<{
  label: string
  type: string
  modelValue: string | number
  placeholder?: string
  options?: Option[]
}>()

defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const fieldId = computed(() => {
  return `field-${props.label.toLowerCase().replace(/\s+/g, '-')}`
})
</script>

<style scoped>
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .field-label {
    font-weight: 600;
    color: #2c3e50;
    font-size: 14px;
    margin-bottom: 4px;
  }

  .input-field,
  .select-field {
    padding: 12px 16px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 16px;
    transition: all 0.3s ease;
    background: white;
  }

    .input-field:focus,
    .select-field:focus {
      outline: none;
      border-color: #007bff;
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
    }

    .input-field::placeholder {
      color: #adb5bd;
    }

  .select-field {
    cursor: pointer;
  }
</style>
