<template>
<div id="app" class="viewport" @click="handleClick">
  <img :src="page.image_url" class="page_image" ref="image" />
  <spinner :show="loading" />
  <router-link v-if="prevUrl" :to="prevUrl" class="left arrow">
    <span class="icon">◀</span>
  </router-link>
  <router-link v-if="nextUrl" :to="nextUrl" class="right arrow">
    <span class="icon">▶</span>
  </router-link>
  <a :href="links.installment_url" class="close">
    <span class="icon">✘</span>
  </a>
  <scrubber-bar v-show="showUI" :numPages="totalPages" @nav="gotoPage" />
</div>
</template>

<script>
import PageCache from './PageCache'
import ScrubberBar from './ScrubberBar.vue'
import Spinner from './Spinner.vue'

export default {
  name: 'viewer',
  components: { ScrubberBar, Spinner },
  data () {
    /* eslint no-underscore-dangle: "off" */
    const wis = window.__INITIAL_STATE__
    const store = PageCache

    store.thread = wis.links.installment_url

    return {
      showUI: true,
      totalPages: wis.total_pages,
      page: wis.page,
      links: wis.links,
      loading: false,
      store,
    }
  },
  computed: {
    currPage () {
      return parseInt(this.$route.params.page, 10) + 1
    },
    prevUrl () {
      return this.getPageRoute(this.currPage - 1)
    },
    nextUrl () {
      return this.getPageRoute(this.currPage + 1)
    },
  },
  methods: {
    getPageRoute (num) {
      return num <= 0 || this.totalPages < num ? undefined : {
        name: 'page',
        params: Object.assign({}, this.$route.params, { page: num - 1 }),
      }
    },
    gotoPage (num) {
      this.$router.push(this.getPageRoute(num))
    },
    handleClick (event) {
      if (event.target === this.$el || event.target === this.$refs.image) {
        this.showUI = !this.showUI
      }
    },
    handlePage (num, url) {
      this.$refs.image.src = url
      this.loading = false
    },
  },
  watch: {
    $route () {
      const num = this.currPage
      const { url, loaded } = this.store.getPage(num)
      if (loaded) {
        this.handlePage(num, url)
      } else {
        this.loading = true
      }
    },
  },
  mounted () {
    this.store.$on('pageloaded', this.handlePage)
  },
}
</script>
