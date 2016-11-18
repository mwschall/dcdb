<template>
<div id="app" class="viewport">
  <img :src="page.image_url" class="page_image" />
  <router-link v-if="links.prev_url" :to="links.prev_url" class="left arrow">
    <span class="icon">◀</span>
  </router-link>
  <router-link v-if="links.next_url" :to="links.next_url" class="right arrow">
    <span class="icon">▶</span>
  </router-link>
  <a :href="links.installment_url" class="close">
    <span class="icon">✘</span>
  </a>
</div>
</template>

<script>
export default {
  name: 'viewer',
  data () {
    /* eslint no-underscore-dangle: "off" */
    return Object.assign({}, window.__INITIAL_STATE__)
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
