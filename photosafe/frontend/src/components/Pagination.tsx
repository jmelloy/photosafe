/* This example requires Tailwind CSS v2.0+ */
import React, { FunctionComponent } from "react";
import { Link } from "react-router-dom";

type PaginationProps = {
  total: number;
  page: number;
  perPage: number;
};

const Pagination: FunctionComponent<PaginationProps> = ({
  total,
  page,
  perPage,
}) => {
  return (
    <nav
      className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 "
      aria-label="Pagination"
    >
      <div className="hidden sm:block">
        <p className="text-sm text-gray-700">
          Showing{" "}
          <span className="font-medium">{(page - 1) * perPage + 1}</span> to{" "}
          <span className="font-medium">{page * perPage}</span> of{" "}
          <span className="font-medium">{total}</span> results
        </p>
      </div>
      <div className="flex-1 flex justify-between sm:justify-end">
        <Link
          to={`/photos/page/${page - 1}`}
          className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          Previous
        </Link>
        <Link
          to={`/photos/page/${page + 1}`}
          className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          Next
        </Link>
      </div>
    </nav>
  );
};
export default Pagination;
