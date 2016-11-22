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
    const ris = this.$root.INITIAL_STATE
    return {
      showUI: true,
      totalPages: ris.total_pages,
      page: ris.page,
      links: ris.links,
      loading: false,
      installment: ris.links.installment_url,
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
    handleClose (event) {
      if (event.keyCode === 27) {
        window.location.href = this.installment
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
    window.addEventListener('keyup', this.handleClose)

    PageCache.$on('pageloaded', this.handlePage)
    PageCache.$on('ready', () => {
      // switch to blob URL and prefetch; request should already be cached
      PageCache.getPage(this.currPage)
    })

    // this kicks the store into action; must happen after event registration
    PageCache.thread = this.installment
  },
  beforeDestroy () {
    window.removeEventListener('keyup', this.handleClose)
  },
}
</script>

<style lang="stylus">
html
body
.viewport
  width 100%
  height 100%
  margin 0

.viewport
  background #000
  user-select none

  a
    text-decoration none

  .icon
    font-size 3rem
    color #222
    text-shadow -1px 0 #ddd, 0 1px #ddd, 1px 0 #ddd, 0 -1px #ddd
    opacity .1
    :hover > ^[1..-1]
      opacity .5

  img
  .arrow
    position absolute
    top 0
    left 0
    right 0
    bottom 0

  img
    margin auto
    max-height 100%
    max-width 100%

.arrow
  width 20%
  .icon
    position absolute
    top 50%
    margin-top -1.5rem
  .left&
    right auto
    .icon
      left 5%
  .right&
    left auto
    .icon
      right 5%
  &.disabled
    cursor default
    .icon
      visibility hidden

.close
  position absolute
  top .5rem
  left .5rem
  padding 1rem
</style>
