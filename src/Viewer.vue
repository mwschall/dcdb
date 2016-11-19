<template>
<div id="app" class="viewport" @click="handleClick">
  <img :src="page.image_url" class="page_image" ref="image" />
  <router-link v-if="links.prev_url" :to="links.prev_url" class="left arrow">
    <span class="icon">◀</span>
  </router-link>
  <router-link v-if="links.next_url" :to="links.next_url" class="right arrow">
    <span class="icon">▶</span>
  </router-link>
  <a :href="links.installment_url" class="close">
    <span class="icon">✘</span>
  </a>
  <scrubber-bar v-show="showUI" :numPages="totalPages" @nav="gotoPage" />
</div>
</template>

<script>
import ScrubberBar from './ScrubberBar.vue'

export default {
  name: 'viewer',
  components: { ScrubberBar },
  data () {
    /* eslint no-underscore-dangle: "off" */
    const wis = window.__INITIAL_STATE__
    return {
      showUI: true,
      totalPages: wis.total_pages,
      page: wis.page,
      links: wis.links,
    }
  },
  methods: {
    getPage (path) {
      const headers = new Headers({
        Accept: 'application/json',
      })

      return fetch(path, {
        method: 'GET',
        redirect: 'follow',
        headers,
      })
    },
    gotoPage (page) {
      this.$router.push({
        name: 'page',
        params: Object.assign({}, this.$route.params, { page: page - 1 }),
      })
    },
    handleClick (event) {
      if (event.target === this.$el || event.target === this.$refs.image) {
        this.showUI = !this.showUI
      }
    },
  },
  watch: {
    $route () {
      this.getPage(this.$route.fullPath)
        .then(response => response.json())
        .then((data) => {
          this.page = data.page
          this.links = data.links
        })
    },
  },
}
</script>
