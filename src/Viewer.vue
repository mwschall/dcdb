<template>
<div
  id="app"
  class="viewport"
  v-touch:tap="handleTap"
  v-touch:swipeleft="handleSwipeLeft"
  v-touch:swiperight="handleSwipeRight"
  >
  <img :src="page.image_url" class="page_image" ref="image" />
  <spinner :show="loading" />
  <router-link :to="nextUrl" class="right arrow" :class="{ disabled: !nextUrl }">
    <span class="icon">▶</span>
  </router-link>
  <router-link :to="prevUrl" class="left arrow" :class="{ disabled: !prevUrl }">
    <span class="icon">◀</span>
  </router-link>
  <a :href="links.installment_url" class="close">
    <span class="icon">✘</span>
  </a>
  <scrubber-bar
    v-show="showUI"
    :currPage="currPage"
    :numPages="totalPages"
    @nav="gotoPage"
    />
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

    return {
      showUI: true,
      totalPages: wis.total_pages,
      page: wis.page,
      links: wis.links,
      loading: false,
      installment: wis.links.installment_url,
    }
  },
  computed: {
    currPage () {
      return parseInt(this.$route.params.page, 10) + 1
    },
    nextUrl () {
      return this.getPageRoute(this.currPage + 1)
    },
    prevUrl () {
      return this.getPageRoute(this.currPage - 1)
    },
  },
  methods: {
    getPageRoute (num) {
      return num <= 0 || this.totalPages < num ? '' : {
        name: 'page',
        params: Object.assign({}, this.$route.params, { page: num - 1 }),
      }
    },
    gotoPage (num) {
      const route = this.getPageRoute(num)
      if (route) {
        this.$router.push(route)
      }
    },
    handleTap (event) {
      if (event.target === this.$el || event.target === this.$refs.image) {
        this.showUI = !this.showUI
      }
    },
    handleSwipeLeft () {
      this.gotoPage(this.currPage + 1)
    },
    handleSwipeRight () {
      this.gotoPage(this.currPage - 1)
    },
    handlePage (num, url) {
      if (num === this.currPage) {
        this.$refs.image.src = url
        this.loading = false
      }
    },
  },
  watch: {
    $route () {
      const num = this.currPage
      const { url, loaded } = PageCache.getPage(num)
      if (loaded) {
        this.handlePage(num, url)
      } else {
        this.loading = true
      }
    },
  },
  mounted () {
    PageCache.$on('pageloaded', this.handlePage)
    PageCache.$on('ready', () => {
      // switch to blob URL and prefetch; request should already be cached
      PageCache.getPage(this.currPage)
    })

    // this kicks the store into action; must happen after event registration
    PageCache.thread = this.installment
  },
}
</script>
