import Vue from 'vue'


const JSONheaders = new Headers({
  Accept: 'application/json',
})

const store = new Vue({
  data: {
    pages: [],
    thread: undefined,
  },
  methods: {
    getPath (path, headers) {
      return fetch(path, {
        method: 'GET',
        redirect: 'follow',
        headers,
      })
    },
    getJson (path) {
      return this.getPath(path, JSONheaders)
    },
    getPage (num) {
      const page = this.pages[num - 1]

      if (!page) {
        throw new Error('We have a problem.')
      }

      if (!page.loaded) {
        this.getPath(page.image_url)
          .then((response) => {
            if (response.ok) {
              response.blob().then((imgBlob) => {
                page.blob = imgBlob
                page.blob_url = URL.createObjectURL(imgBlob)
                page.loaded = true
                this.$emit('pageloaded', num, page.blob_url)
              })
            }
          })
      }

      return { url: page.blob_url, loaded: !!page.loaded }
    },
  },
  watch: {
    thread (url) {
      this.getJson(url)
        .then(response => response.json())
        .then((data) => {
          this.pages = data.pages
          this.$emit('ready')
        })
    },
  },
})

export default store
