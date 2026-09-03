import '@testing-library/jest-dom/vitest'

// jsdom doesn't implement object URLs, which UploadPage uses for the image preview.
if (typeof URL.createObjectURL !== 'function') {
  URL.createObjectURL = () => 'blob:mock'
  URL.revokeObjectURL = () => {}
}
