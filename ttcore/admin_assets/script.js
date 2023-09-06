export default {
	data() {
		return {
			messages: [],
			models: null,
			showModel: null,
			modelResults: null,
			HEADERS: ['internal_name', 'title_en', 'name', 'title', 'updated'],
			editModel: null,
			newModel: null,
			page: 1,
			MAX_PAGE_ITEMS: 10,
			statusDevelopmentChoice: ['draft', 'auto-draft', 'publish', 'inherit', 'pending', 'private'],
			licenseDevelopmentChoice: [
				{label: 'with license', code: 1},
				{label: 'without license', code: 2}
			],
			commissionDevelopmentChoice: ['unset', 'within_1_month', 'within_6_months', 'more_than_6_months'],
			search: null,
			typeTagChoice: [
				{ label: 'Building status', code: 1 },
				{ label: 'Close to', code: 2 },
				{ label: 'Builders', code: 3 },
				{ label: 'Amenities', code: 4 },
				{ label: 'Views', code: 5 },
				{ label: 'Purchase Agreement', code: 6 },
				{ label: 'Location', code: 7 }
			]
		}
	},
	methods: {
		showFlash(msg, status = 'info', delay = 3000) {
			this.messages.push({message: msg, state: status});
			
			setTimeout(() => {
				this.messages.shift();
			}, delay);
		},
		searchModels(model, q) {
			let data = {
				name: model,
				page: this.page
			}
			
			if(q) {
				data['q'] = q;
			}

			return this.$api.post('admin_interface/admin_search_instance', data) //(it is needed to pass name of model, and search passing q, order_by, page, etc. as usual)
		},
		searchModelsBasic(q) {
			this.searchModels(this.showModel.model, q)
			.then(res => {
				this.modelResults = res.data.data;
				this.no_pages = Math.ceil(res.data.no_objects / res.data.paginate_by)
			})
		},
		updateModel(updateData) {
			let data = {
				name: this.showModel.model,
				identifier: { pid: this.editModel.pid }
			}
			data['data'] = updateData

			this.$api.post('admin_interface/admin_update_instance', data)
			.then(res => {
				this.showFlash('Saved', 'success')
			})
		},
		createModel() {
			let data = {
				name: this.showModel.model,
				data: this.newModel
			}

			this.$api.post('admin_interface/admin_create_instance', data)
			.then(res => {
				if(res.data.msg == 'ok') {
					this.showFlash('New model was added', 'success')
					this.newModel = null;
					this.searchModelsBasic()
				} else {
					this.showFlash(res.data.msg, 'error')
				}
			})
		},
		fetchModels() {
			this.$api.post('admin_interface/admin_get_models', {})
			.then(res => {
				this.models = res.data.data;

				this.initCheck()
			})
		},
		openModel(model) {
			this.$router.push({query: { model: model.model }})
			this.showModel = model
			this.editModel = null
			this.newModel = null

			this.searchModelsBasic()
		},
		editModelInfo(item) {
			this.$router.push({query: { model: this.showModel.model, edit: item.pid }})
			this.editModel = item
			this.newModel = null
		},
		formatDate(timestamp) {
			var date = new Date(timestamp * 1000);
			return `${date.getDate()}/${date.getMonth()+1}/${date.getFullYear()} ${date.getHours()}:${('0' + date.getMinutes()).slice(-2)}`;
		},
		closeModelInfo() {
			this.editModel = null
			this.$router.push({query: { model: this.showModel.model }})
		},
		initCheck() {
			if(this.modelDetail) {
				this.showModel = this.models.find(item => item.model == this.modelDetail)
				this.searchModelsBasic()
			}
			if(this.modelDetailInfo) {
				this.searchModels(this.showModel.model, this.modelDetailInfo)
				.then(res => {
					this.editModel = res.data.data[0]
				})
			}

			if(!this.modelDetail && !this.modelDetailInfo) {
				this.showModel = this.models[0]
				this.$router.push({query: { model: this.showModel.model }})
				this.searchModelsBasic()
			}
		},
		changeModelInfo(key, val) {
			let data = {}
			data[key] = val

			this.updateModel(data)
		},
		addNewModel() {
			this.editModel = null
			this.newModel = {}

			this.showModel.required_fields.forEach(item => {
				if(item != 'pid') {
					this.newModel[item] = ''
				}
			})
		},
		closeNewModel() {
			this.newModel = null;
		},
		goTo(n) {
			this.page = n;
			this.searchModelsBasic()
		},
		goNext() {
			this.page++;
			this.searchModelsBasic()
		},
		goPrev() {
			this.page--;
			this.searchModelsBasic()
		},
		autologin() {
			let token = window.location.search.replace('?authtoken=', '')
			localStorage.setItem('token', token)
			this.$api.defaults.headers.common['Authorization'] = `bearer ${token}`

			this.fetchModels();
		}
	},
	created() {
		if(window.location.search.includes('authtoken=')) {
			this.autologin()
		} else {
			this.fetchModels()
		}
	},
	computed: {
		modelDetail() {
			return this.$route.query.model
		},
		modelDetailInfo() {
			return this.$route.query.edit
		},
		commonHeaders() {
			return this.HEADERS.filter(item => {
				return this.modelResults[0][item]
			})
		},
		pages() {
			var list = Array(this.no_pages).fill().map((_, i) => i+1);
			var min = this.no_pages < this.MAX_PAGE_ITEMS ? 1 : this.page < this.no_pages - this.MAX_PAGE_ITEMS ? this.page : this.no_pages - this.MAX_PAGE_ITEMS;
			var max = this.no_pages < this.MAX_PAGE_ITEMS ? this.MAX_PAGE_ITEMS : this.page < this.no_pages - this.MAX_PAGE_ITEMS ? this.page + this.MAX_PAGE_ITEMS : this.no_pages;
			return list.slice(min - 1, max);
		}
	}
}