class ProductsController < BaseController

  def index
    @products = Product.all
  end

end