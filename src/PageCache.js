import Vue from 'vue'


const JSONheaders = new Headers({
  Accept: 'application/json',
})

const store = new Vue({
  props: {
    ensureForward: {
      type: Number,
      default: 2,
    },
    retainBackward: {
      type: Number,
      default: 1,
    },
  },
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

      this.loadPage(num)
      this.$nextTick(() => {
        for (let n = num - this.retainBackward; n <= num + this.ensureForward; n += 1) {
          if (n !== num) {
            this.loadPage(n)
          }
        }
      })

      return { url: page.blob_url, loaded: !!page.loaded }
    },
    loadPage (num) {
      const page = this.pages[num - 1]
      if (page && !page.loaded) {
        // TODO: may need to use blob-util.imgSrcToBlob for wider support
        this.getPath(page.image_url)
          .then((response) => {
            if (response.ok) {
              response.blob().then((blob) => {
                this.setBlob(num, blob)
                this.$emit('pageloaded', num, page.blob_url)
              })
            }
          })
      }
    },
    setBlob (num, blob) {
      const page = this.pages[num - 1]
      if (page) {
        page.blob_url = URL.createObjectURL(blob)
        page.loaded = true
      }
    },
    killBlob (num) {
      const page = this.pages[num - 1]
      if (page && page.loaded) {
        URL.revokeObjectURL(page.blob_url)
      }
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
